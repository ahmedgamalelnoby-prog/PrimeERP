import { useEffect, useState } from "react";
import env from "@/shared/config/env";
import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";

type SallaEmbedded = {
  init: (options?: { debug?: boolean }) => Promise<unknown>;
  auth: { getToken: () => string | null };
  ready: () => void;
  destroy: () => void;
};

declare global {
  interface Window {
    Salla?: { embedded?: SallaEmbedded };
  }
}

const SDK_URL = "https://unpkg.com/@salla.sa/embedded-sdk/dist/umd/index.js";

function loadSallaSdk(): Promise<SallaEmbedded> {
  return new Promise((resolve, reject) => {
    if (window.Salla?.embedded) {
      resolve(window.Salla.embedded);
      return;
    }
    const script = document.createElement("script");
    script.src = SDK_URL;
    script.async = true;
    script.onload = () => {
      const embedded = window.Salla?.embedded;
      if (embedded) resolve(embedded);
      else reject(new Error("Salla Embedded SDK did not initialize."));
    };
    script.onerror = () => reject(new Error("Unable to load Salla Embedded SDK."));
    document.head.appendChild(script);
  });
}

export default function SallaEmbeddedPage() {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    let embedded: SallaEmbedded | undefined;

    const bootstrap = async () => {
      try {
        embedded = await loadSallaSdk();
        await embedded.init({ debug: false });
        const token = embedded.auth.getToken();
        if (!token) throw new Error("Salla session token is missing.");

        const response = await client.post(
          "/salla-app/embedded/session",
          { salla_token: token },
        );
        const payload = response.data;
        const ticket = payload?.sso_ticket;
        if (!ticket) throw new Error("PrimeERP did not return an SSO ticket.");

        const exchange = await client.post(
          "/salla-app/sso/exchange",
          null,
          { params: { ticket } },
        );
        const session = exchange.data;
        if (!session?.access_token) {
          throw new Error("PrimeERP did not return an access token.");
        }

        storage.setAccessToken(session.access_token);
        embedded.ready();
        window.location.replace("/dashboard");
      } catch (cause) {
        if (!mounted) return;
        console.error("Salla embedded bootstrap failed:", cause);
        setError(cause instanceof Error ? cause.message : "Unable to connect to Salla.");
        try {
          embedded?.destroy();
        } catch {
          // Ignore SDK teardown errors.
        }
      }
    };

    void bootstrap();
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-6" dir="rtl">
      <div className="w-full max-w-md rounded-2xl border bg-card p-8 text-center shadow-sm">
        {!error ? (
          <>
            <h1 className="text-2xl font-bold">PrimeERP</h1>
            <p className="mt-3 text-sm text-muted-foreground">
              جاري التحقق من متجر Salla وفتح حسابك تلقائياً...
            </p>
          </>
        ) : (
          <>
            <h1 className="text-xl font-bold text-destructive">تعذر فتح PrimeERP</h1>
            <p className="mt-3 text-sm text-muted-foreground">{error}</p>
          </>
        )}
      </div>
    </div>
  );
}
