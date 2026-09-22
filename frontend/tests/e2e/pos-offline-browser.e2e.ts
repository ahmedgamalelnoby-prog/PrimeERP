import { test, expect, chromium, type BrowserContext, type Page, type Route } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const BASE_URL = process.env.POS_E2E_BASE_URL ?? "http://127.0.0.1:4173";
const API_ORIGIN = process.env.POS_E2E_API_ORIGIN ?? "http://127.0.0.1:8000";

type FixtureState = {
  checkoutBodies: Array<Record<string, unknown>>;
  failNextCheckout: boolean;
};

function json(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function installApiFixtures(context: BrowserContext, state: FixtureState) {
  await context.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (!url.href.startsWith(API_ORIGIN)) return route.continue();

    if (url.pathname.endsWith("/identity/me")) {
      return json(route, {
        id: 1, tenant_id: 1, username: "pos-e2e", email: "pos-e2e@example.test",
        full_name: "POS E2E", role_id: 1, is_active: true,
        is_superuser: true, is_platform_admin: false,
        preferred_language: "ar", tenant_slug: "pos-e2e",
        tenant_name: "POS E2E", tenant_status: "active",
        subscription_status: "active", enabled_modules: ["sales", "pos"],
      });
    }

    if (url.pathname.endsWith("/pos/outlets")) {
      return json(route, [{ id: 10, name: "Restaurant Sea", warehouse_id: 20 }]);
    }
    if (url.pathname.endsWith("/pos/stations")) {
      return json(route, [{ id: 30, name: "Main Kitchen", station_type: "kitchen" }]);
    }
    if (url.pathname.endsWith("/pos/terminals")) {
      return json(route, [{ id: 40, name: "POS-01", code: "POS-01", outlet_id: 10 }]);
    }
    if (url.pathname.endsWith("/catalog/menus")) {
      return json(route, [{
        id: 50, name_ar: "Main Menu",
        items: [{ id: 60, product_id: 70, sale_price_override: 100 }],
      }]);
    }
    if (url.pathname.endsWith("/pos/sales")) return json(route, []);
    if (url.pathname.endsWith("/pos/warehouses")) {
      return json(route, [{ id: 20, name: "Restaurant Sea Store", code: "SEA-01", is_central: false }]);
    }

    if (url.pathname.endsWith("/pos/checkout")) {
      const body = route.request().postDataJSON() as Record<string, unknown>;
      state.checkoutBodies.push(body);
      if (state.failNextCheckout) {
        state.failNextCheckout = false;
        return route.abort("failed");
      }
      return json(route, {
        id: state.checkoutBodies.length,
        number: body.number,
        status: "confirmed",
      });
    }

    return json(route, {});
  });
}

async function openPos(context: BrowserContext, options: { offlineAfterNavigation?: boolean } = {}): Promise<Page> {
  const page = await context.newPage();

  // /pos is protected. AuthProvider only calls /identity/me when an access
  // token already exists, so seed a deterministic E2E token BEFORE navigation.
  // This prevents the real application from redirecting to /login.
  await page.addInitScript(() => {
    localStorage.setItem("access_token", "pos-e2e-access-token");
    localStorage.setItem("refresh_token", "pos-e2e-refresh-token");
    localStorage.setItem("tenant_id", "1");
    localStorage.setItem("company_id", "1");
  });

  await page.goto(`${BASE_URL}/pos`, { waitUntil: "commit", timeout: 15000 });
  await expect(page.getByRole("heading", { name: "Restaurant & Hotel POS" })).toBeVisible();
  if (options.offlineAfterNavigation) {
    await context.setOffline(true);
    await expect.poll(() => page.evaluate(() => navigator.onLine), { timeout: 5000 }).toBe(false);
  }
  return page;
}

async function prepareSale(page: Page) {
  await page.getByPlaceholder("Customer/Partner ID").fill("900");
  const selects = page.locator("select");
  await selects.nth(0).selectOption("40");
  await selects.nth(1).selectOption("50");
  await selects.nth(2).selectOption("60");
}

async function submitSale(page: Page) {
  await page.getByRole("button", { name: "إرسال الطلب وتنفيذ البيع" }).click();
}

test("restaurant POS survives offline orders, browser restart, retry, and response-loss", async ({}, testInfo) => {
  const profile = testInfo.outputPath("persistent-pos-profile");
  fs.mkdirSync(path.dirname(profile), { recursive: true });

  const state: FixtureState = { checkoutBodies: [], failNextCheckout: false };
  let context = await chromium.launchPersistentContext(profile, {
    headless: true,
    serviceWorkers: "allow",
  });

  try {
    // The protected /pos route loads AuthProvider first. Install the API fixtures
    // before the first navigation so /identity/me is deterministic as well.
    await installApiFixtures(context, state);
    const page = await openPos(context);

    // Keep this browser contract focused on the POS offline queue, durable
    // IndexedDB state, reconnect sync, retry, and response-loss handling.
    // Service-worker availability is verified by the dedicated offline-artifact
    // gate; registering/awaiting a SW here can block indefinitely under Vite and
    // mask the actual POS contract being tested.
    await expect(page.getByText("● Online")).toBeVisible();

    await context.setOffline(true);
    await expect.poll(() => page.evaluate(() => navigator.onLine), { timeout: 5000 }).toBe(false);
    await expect(page.getByText("● Offline — الطلبات تُحفظ محليًا")).toBeVisible();

    for (let i = 0; i < 3; i++) {
      await prepareSale(page);
      await submitSale(page);
      await expect(page.getByText("تم حفظ الطلب محليًا. سيتم ترحيله تلقائيًا عند عودة الإنترنت.")).toBeVisible();
    }
    await expect(page.getByText("3 طلب في انتظار المزامنة")).toBeVisible();

    const firstDeviceId = await page.evaluate(() => localStorage.getItem("primeerp-pos-device-id"));
    expect(firstDeviceId).toBeTruthy();

    const queuedBeforeRestart = await page.evaluate(() =>
      new Promise<number>((resolve, reject) => {
        const request = indexedDB.open("primeerp-pos", 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const tx = request.result.transaction("checkout_queue", "readonly");
          const getAll = tx.objectStore("checkout_queue").getAll();
          getAll.onsuccess = () => resolve(getAll.result.length);
          getAll.onerror = () => reject(getAll.error);
        };
      })
    );
    expect(queuedBeforeRestart).toBe(3);

    // Close the browser context while offline, then launch a NEW persistent
    // browser context against the same profile. The new context starts online,
    // which is required to load the Vite application shell before simulating
    // the offline network state.
    await page.close();
    await context.close();
    context = await chromium.launchPersistentContext(profile, {
      headless: true,
      serviceWorkers: "allow",
    });
    await installApiFixtures(context, state);

    const reopened = await openPos(context);
    await context.setOffline(true);
    await expect.poll(() => reopened.evaluate(() => navigator.onLine), { timeout: 5000 }).toBe(false);
    await expect(reopened.getByText("● Offline — الطلبات تُحفظ محليًا")).toBeVisible();
    await expect(reopened.getByText("3 طلب في انتظار المزامنة")).toBeVisible();

    const reopenedDeviceId = await reopened.evaluate(() => localStorage.getItem("primeerp-pos-device-id"));
    expect(reopenedDeviceId).toBe(firstDeviceId);

    const queuedAfterRestart = await reopened.evaluate(() =>
      new Promise<number>((resolve, reject) => {
        const request = indexedDB.open("primeerp-pos", 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => {
          const tx = request.result.transaction("checkout_queue", "readonly");
          const getAll = tx.objectStore("checkout_queue").getAll();
          getAll.onsuccess = () => resolve(getAll.result.length);
          getAll.onerror = () => reject(getAll.error);
        };
      })
    );
    expect(queuedAfterRestart).toBe(3);

    await context.setOffline(false);
    await expect.poll(
      () => reopened.evaluate(() => navigator.onLine),
      { timeout: 5000 }
    ).toBe(true);
    await expect.poll(
      () => state.checkoutBodies.length,
      { timeout: 30000, intervals: [250, 500, 1000, 2000] }
    ).toBe(3);
    await expect.poll(
      () => reopened.getByText(/طلب في انتظار المزامنة/).count(),
      { timeout: 30000, intervals: [250, 500, 1000, 2000] }
    ).toBe(0);

    const numbers = state.checkoutBodies.map((x) => String(x.number));
    expect(new Set(numbers).size).toBe(3);

    state.failNextCheckout = true;
    await prepareSale(reopened);
    await submitSale(reopened);
    await expect(reopened.getByText(/تم حفظ الطلب محليًا|تعذر الاتصال بالخادم/)).toBeVisible();

    await expect.poll(() => state.checkoutBodies.length, { timeout: 10000 }).toBe(4);
    await expect.poll(
      () => reopened.getByText(/طلب في انتظار المزامنة/).count(),
      { timeout: 10000 }
    ).toBeGreaterThan(0);

    await context.setOffline(true);
    await expect.poll(
      () => reopened.evaluate(() => navigator.onLine),
      { timeout: 5000 }
    ).toBe(false);

    await context.setOffline(false);
    await expect.poll(
      () => reopened.evaluate(() => navigator.onLine),
      { timeout: 5000 }
    ).toBe(true);
    await expect.poll(
      () => state.checkoutBodies.length,
      { timeout: 30000, intervals: [250, 500, 1000, 2000] }
    ).toBe(5);
    await expect.poll(
      () => reopened.getByText(/طلب في انتظار المزامنة/).count(),
      { timeout: 30000, intervals: [250, 500, 1000, 2000] }
    ).toBe(0);

    expect(new Set(state.checkoutBodies.map((x) => String(x.number))).size).toBe(4);
  } finally {
    await context.close();
  }
});
