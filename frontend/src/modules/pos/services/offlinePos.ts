import client from "@/shared/api/client";

export type PosCheckoutPayload = {
  company_id: number;
  partner_id: number;
  warehouse_id: number;
  number: string;
  payment_date: string;
  method: string;
  terminal_id: number;
  lines: Array<{
    menu_item_id?: number;
    item_id?: number;
    variant_id?: number;
    quantity: number;
    unit_price?: number;
    discount_percent?: number;
  }>;
};

export type OfflineQueueItem = {
  id: string;
  createdAt: string;
  attempts: number;
  status: "pending" | "syncing" | "failed";
  lastError?: string;
  payload: PosCheckoutPayload;
};

const DB_NAME = "primeerp-pos";
const DB_VERSION = 1;
const QUEUE_STORE = "checkout_queue";
const CACHE_STORE = "pos_cache";
const DEVICE_KEY = "primeerp-pos-device-id";

function uuid(): string {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
  return \`\${Date.now()}-\${Math.random().toString(36).slice(2)}\`;
}

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(QUEUE_STORE)) {
        const store = db.createObjectStore(QUEUE_STORE, { keyPath: "id" });
        store.createIndex("status", "status", { unique: false });
        store.createIndex("createdAt", "createdAt", { unique: false });
      }
      if (!db.objectStoreNames.contains(CACHE_STORE)) db.createObjectStore(CACHE_STORE, { keyPath: "key" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function transaction<T>(
  storeName: string,
  mode: IDBTransactionMode,
  work: (store: IDBObjectStore, resolve: (value: T) => void, reject: (reason?: unknown) => void) => void,
): Promise<T> {
  const db = await openDb();
  return new Promise<T>((resolve, reject) => {
    const tx = db.transaction(storeName, mode);
    work(tx.objectStore(storeName), resolve, reject);
    tx.oncomplete = () => db.close();
    tx.onerror = () => reject(tx.error);
    tx.onabort = () => reject(tx.error);
  });
}

export function getDeviceId(): string {
  const existing = localStorage.getItem(DEVICE_KEY);
  if (existing) return existing;
  const value = uuid();
  localStorage.setItem(DEVICE_KEY, value);
  return value;
}

export async function cachePosData(key: string, value: unknown): Promise<void> {
  await transaction<void>(CACHE_STORE, "readwrite", (store, resolve, reject) => {
    const request = store.put({ key, value, cachedAt: new Date().toISOString() });
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function readPosCache<T>(key: string): Promise<T | null> {
  return transaction<T | null>(CACHE_STORE, "readonly", (store, resolve, reject) => {
    const request = store.get(key);
    request.onsuccess = () => resolve(request.result?.value ?? null);
    request.onerror = () => reject(request.error);
  });
}

export async function enqueueCheckout(payload: PosCheckoutPayload): Promise<OfflineQueueItem> {
  const item: OfflineQueueItem = {
    id: uuid(),
    createdAt: new Date().toISOString(),
    attempts: 0,
    status: "pending",
    payload,
  };
  await transaction<void>(QUEUE_STORE, "readwrite", (store, resolve, reject) => {
    const request = store.add(item);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
  return item;
}

export async function listCheckoutQueue(): Promise<OfflineQueueItem[]> {
  return transaction<OfflineQueueItem[]>(QUEUE_STORE, "readonly", (store, resolve, reject) => {
    const request = store.getAll();
    request.onsuccess = () => resolve((request.result as OfflineQueueItem[]).sort((a, b) => a.createdAt.localeCompare(b.createdAt)));
    request.onerror = () => reject(request.error);
  });
}

async function updateQueueItem(item: OfflineQueueItem): Promise<void> {
  await transaction<void>(QUEUE_STORE, "readwrite", (store, resolve, reject) => {
    const request = store.put(item);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

async function removeQueueItem(id: string): Promise<void> {
  await transaction<void>(QUEUE_STORE, "readwrite", (store, resolve, reject) => {
    const request = store.delete(id);
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
}

export async function flushCheckoutQueue(): Promise<{ synced: number; failed: number }> {
  if (!navigator.onLine) return { synced: 0, failed: 0 };
  let synced = 0;
  let failed = 0;
  const queue = await listCheckoutQueue();

  for (const item of queue) {
    item.status = "syncing";
    item.attempts += 1;
    await updateQueueItem(item);
    try {
      await client.post("/pos/checkout", item.payload);
      await removeQueueItem(item.id);
      synced += 1;
    } catch (error: any) {
      item.status = "failed";
      item.lastError = error?.response?.data?.detail || error?.message || "Sync failed";
      await updateQueueItem(item);
      failed += 1;
      if (!error?.response) break;
    }
  }
  return { synced, failed };
}

export function installOfflineSync(onChange?: () => void): () => void {
  const trigger = () => { void flushCheckoutQueue().finally(() => onChange?.()); };
  window.addEventListener("online", trigger);
  const timer = window.setInterval(trigger, 15000);
  trigger();
  return () => {
    window.removeEventListener("online", trigger);
    window.clearInterval(timer);
  };
}

export function registerOfflineServiceWorker(): void {
  if (!("serviceWorker" in navigator)) return;
  window.addEventListener("load", () => { void navigator.serviceWorker.register("/pos-sw.js", { scope: "/" }); });
}
