import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import client from "@/shared/api/client";

type Recipe = {
  id: number;
  name_ar?: string;
  name?: string;
  code?: string;
  yield_quantity?: number;
  lines?: unknown[];
};

type Warehouse = { id: number; code: string; name: string; is_active: boolean };
type Location = { id: number; code: string; name: string; is_active: boolean; is_virtual: boolean };

type WorkOrder = {
  id: number;
  number: string;
  recipe_id: number;
  source_location_id: number;
  destination_location_id: number;
  planned_quantity: number;
  produced_quantity: number | null;
  status: "planned" | "released" | "completed" | "cancelled" | string;
  lines: Array<{ id: number; ingredient_item_id: number; quantity_per_output: number; issued_quantity: number | null }>;
};

const companyId = () => Number(localStorage.getItem("company_id")) || null;

const statusLabels: Record<string, string> = {
  planned: "مخطط",
  released: "تم الإصدار",
  completed: "مكتمل",
  cancelled: "ملغي",
};

export default function ManufacturingPage() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [sourceLocations, setSourceLocations] = useState<Location[]>([]);
  const [destinationLocations, setDestinationLocations] = useState<Location[]>([]);
  const [recipeId, setRecipeId] = useState("");
  const [number, setNumber] = useState("");
  const [sourceWarehouseId, setSourceWarehouseId] = useState("");
  const [destinationWarehouseId, setDestinationWarehouseId] = useState("");
  const [sourceLocationId, setSourceLocationId] = useState("");
  const [destinationLocationId, setDestinationLocationId] = useState("");
  const [plannedQuantity, setPlannedQuantity] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const company = companyId();

  const load = useCallback(async () => {
    if (!company) return;
    try {
      const [recipeResponse, orderResponse, warehouseResponse] = await Promise.all([
        client.get("/manufacturing/bom", { params: { company_id: company } }),
        client.get("/manufacturing/work-orders", { params: { company_id: company } }),
        client.get("/inventory/warehouses", { params: { company_id: company, include_central: true } }),
      ]);
      setRecipes(recipeResponse.data);
      setOrders(orderResponse.data);
      setWarehouses(warehouseResponse.data.filter((warehouse: Warehouse) => warehouse.is_active));
      setError("");
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل بيانات التصنيع");
    }
  }, [company]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!company || !sourceWarehouseId) { setSourceLocations([]); setSourceLocationId(""); return; }
    client.get("/inventory/locations", { params: { company_id: company, warehouse_id: Number(sourceWarehouseId) } })
      .then((response) => setSourceLocations(response.data.filter((location: Location) => location.is_active && !location.is_virtual)))
      .catch((e: any) => setError(e?.response?.data?.detail || "تعذر تحميل مواقع صرف الخامات"));
    setSourceLocationId("");
  }, [company, sourceWarehouseId]);

  useEffect(() => {
    if (!company || !destinationWarehouseId) { setDestinationLocations([]); setDestinationLocationId(""); return; }
    client.get("/inventory/locations", { params: { company_id: company, warehouse_id: Number(destinationWarehouseId) } })
      .then((response) => setDestinationLocations(response.data.filter((location: Location) => location.is_active && !location.is_virtual)))
      .catch((e: any) => setError(e?.response?.data?.detail || "تعذر تحميل مواقع استلام المنتج"));
    setDestinationLocationId("");
  }, [company, destinationWarehouseId]);

  async function createOrder(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!company) return;
    setSaving(true);
    setError("");
    setNotice("");
    try {
      await client.post("/manufacturing/work-orders", {
        company_id: company,
        recipe_id: Number(recipeId),
        number: number.trim(),
        source_location_id: Number(sourceLocationId),
        destination_location_id: Number(destinationLocationId),
        planned_quantity: Number(plannedQuantity),
      });
      setNumber("");
      setPlannedQuantity("");
      setNotice("تم إنشاء أمر التشغيل. راجعه ثم أصدره لبدء الإنتاج.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر إنشاء أمر التشغيل");
    } finally {
      setSaving(false);
    }
  }

  async function act(order: WorkOrder, action: "release" | "complete" | "cancel") {
    if (!company) return;
    let producedQuantity: number | undefined;
    if (action === "complete") {
      const answer = window.prompt("أدخل الكمية المنتجة فعلياً:");
      if (answer === null) return;
      producedQuantity = Number(answer);
      if (!Number.isFinite(producedQuantity) || producedQuantity <= 0) {
        setError("أدخل كمية إنتاج موجبة وصحيحة.");
        return;
      }
    }
    if (action === "cancel" && !window.confirm("سيتم عكس حركات المخزون والقيد المرتبط بأمر التشغيل. هل تريد المتابعة؟")) return;

    setBusyId(order.id);
    setError("");
    setNotice("");
    try {
      await client.post(
        `/manufacturing/work-orders/${order.id}/${action}`,
        action === "complete" ? { produced_quantity: producedQuantity } : {},
        { params: { company_id: company } },
      );
      setNotice(action === "release" ? "تم إصدار أمر التشغيل." : action === "complete" ? "اكتمل الإنتاج وتم ترحيل الخامات والمنتج التام." : "تم إلغاء الأمر وعكس حركاته.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تنفيذ الإجراء");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">التصنيع</h1>
        <p className="text-sm text-muted-foreground">
          أوامر تشغيل مرتبطة بالوصفات وحركات المخزون وتكلفة المنتج التام.
        </p>
      </header>

      {error && <div role="alert" className="rounded-xl border bg-destructive/10 p-3">{error}</div>}
      {notice && <div role="status" className="rounded-xl border bg-primary/10 p-3">{notice}</div>}
      {!company && <div role="alert" className="rounded-xl border p-3">اختر شركة قبل إدارة أوامر التشغيل.</div>}

      <form onSubmit={createOrder} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-2 xl:grid-cols-3">
        <h2 className="font-semibold md:col-span-2 xl:col-span-3">إنشاء أمر تشغيل</h2>
        <label className="space-y-1 text-sm">
          <span>الوصفة</span>
          <select required value={recipeId} onChange={(event) => setRecipeId(event.target.value)} className="w-full rounded border bg-background px-3 py-2">
            <option value="">اختر وصفة</option>
            {recipes.map((recipe) => (
              <option key={recipe.id} value={recipe.id}>{recipe.name_ar || recipe.name || recipe.code || `وصفة ${recipe.id}`}</option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-sm">
          <span>رقم أمر التشغيل</span>
          <input required maxLength={60} value={number} onChange={(event) => setNumber(event.target.value)} className="w-full rounded border bg-background px-3 py-2" />
        </label>
        <label className="space-y-1 text-sm">
          <span>كمية الإنتاج المخططة</span>
          <input required min="0.0001" step="0.0001" type="number" value={plannedQuantity} onChange={(event) => setPlannedQuantity(event.target.value)} className="w-full rounded border bg-background px-3 py-2" />
        </label>
        <label className="space-y-1 text-sm">
          <span>مخزن صرف الخامات</span>
          <select required value={sourceWarehouseId} onChange={(event) => setSourceWarehouseId(event.target.value)} className="w-full rounded border bg-background px-3 py-2"><option value="">اختر مخزن الصرف</option>{warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name} ({warehouse.code})</option>)}</select>
        </label>
        <label className="space-y-1 text-sm">
          <span>موقع صرف الخامات</span>
          <select required value={sourceLocationId} onChange={(event) => setSourceLocationId(event.target.value)} className="w-full rounded border bg-background px-3 py-2" disabled={!sourceWarehouseId}><option value="">اختر موقع الصرف</option>{sourceLocations.map((location) => <option key={location.id} value={location.id}>{location.name} ({location.code})</option>)}</select>
        </label>
        <label className="space-y-1 text-sm">
          <span>مخزن استلام المنتج التام</span>
          <select required value={destinationWarehouseId} onChange={(event) => setDestinationWarehouseId(event.target.value)} className="w-full rounded border bg-background px-3 py-2"><option value="">اختر مخزن الاستلام</option>{warehouses.map((warehouse) => <option key={warehouse.id} value={warehouse.id}>{warehouse.name} ({warehouse.code})</option>)}</select>
        </label>
        <label className="space-y-1 text-sm">
          <span>موقع استلام المنتج التام</span>
          <select required value={destinationLocationId} onChange={(event) => setDestinationLocationId(event.target.value)} className="w-full rounded border bg-background px-3 py-2" disabled={!destinationWarehouseId}><option value="">اختر موقع الاستلام</option>{destinationLocations.map((location) => <option key={location.id} value={location.id}>{location.name} ({location.code})</option>)}</select>
        </label>
        <button disabled={!company || saving} className="self-end rounded bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">
          {saving ? "جارٍ الحفظ…" : "إنشاء أمر تشغيل"}
        </button>
      </form>

      <div className="overflow-hidden rounded-2xl border bg-card">
        <div className="border-b p-4 font-semibold">أوامر التشغيل</div>
        {orders.length === 0 ? (
          <p className="p-4 text-sm text-muted-foreground">لا توجد أوامر تشغيل لهذه الشركة.</p>
        ) : (
          <div className="divide-y">
            {orders.map((order) => (
              <article key={order.id} className="space-y-3 p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-semibold">{order.number}</h3>
                    <p className="text-sm text-muted-foreground">
                      وصفة #{order.recipe_id} · مخطط {order.planned_quantity} · منتج {order.produced_quantity ?? "—"} · {order.lines?.length ?? 0} مكونات
                    </p>
                    <p className="text-xs text-muted-foreground">
                      صرف من موقع #{order.source_location_id} إلى موقع #{order.destination_location_id}
                    </p>
                  </div>
                  <span className="rounded-full border px-3 py-1 text-sm">{statusLabels[order.status] || order.status}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {order.status === "planned" && <button disabled={busyId === order.id} onClick={() => void act(order, "release")} className="rounded border px-3 py-1.5 disabled:opacity-50">إصدار</button>}
                  {order.status === "released" && <button disabled={busyId === order.id} onClick={() => void act(order, "complete")} className="rounded bg-primary px-3 py-1.5 text-primary-foreground disabled:opacity-50">تسجيل الإنتاج والترحيل</button>}
                  {(order.status === "planned" || order.status === "released" || order.status === "completed") && <button disabled={busyId === order.id} onClick={() => void act(order, "cancel")} className="rounded border border-destructive/50 px-3 py-1.5 text-destructive disabled:opacity-50">إلغاء وعكس الحركات</button>}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
