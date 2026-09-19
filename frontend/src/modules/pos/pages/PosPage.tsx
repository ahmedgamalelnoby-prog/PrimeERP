import { useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";

type AnyRow = Record<string, any>;
const companyId = () => Number(localStorage.getItem("company_id")) || 0;

export default function PosPage() {
  const cid = companyId();
  const [outlets, setOutlets] = useState<AnyRow[]>([]);
  const [stations, setStations] = useState<AnyRow[]>([]);
  const [terminals, setTerminals] = useState<AnyRow[]>([]);
  const [menus, setMenus] = useState<AnyRow[]>([]);
  const [sales, setSales] = useState<AnyRow[]>([]);
  const [warehouses, setWarehouses] = useState<AnyRow[]>([]);
  const [queue, setQueue] = useState<AnyRow[]>([]);
  const [error, setError] = useState("");
  const [branchId, setBranchId] = useState("");
  const [selectedOutlet, setSelectedOutlet] = useState("");
  const [selectedTerminal, setSelectedTerminal] = useState("");
  const [selectedStation, setSelectedStation] = useState("");
  const [selectedMenu, setSelectedMenu] = useState("");
  const [selectedMenuItem, setSelectedMenuItem] = useState("");
  const [partnerId, setPartnerId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [qty, setQty] = useState("1");
  const [method, setMethod] = useState("cash");
  const [tab, setTab] = useState<"sale" | "setup" | "kds">("sale");

  const [outletForm, setOutletForm] = useState({ code: "", name: "", outlet_type: "restaurant" });
  const [stationForm, setStationForm] = useState({ code: "", name: "", station_type: "kitchen" });
  const [terminalForm, setTerminalForm] = useState({ code: "", name: "", device_identifier: "" });
  const [priceListId, setPriceListId] = useState("");
  const [outletWarehouseId, setOutletWarehouseId] = useState("");

  const activeMenu = useMemo(() => menus.find(x => String(x.id) === selectedMenu), [menus, selectedMenu]);
  const activeMenuItem = useMemo(() => activeMenu?.items?.find((x: AnyRow) => String(x.id) === selectedMenuItem), [activeMenu, selectedMenuItem]);

  async function load() {
    if (!cid) return;
    try {
      const [o, s, t, m, v, w] = await Promise.all([
        client.get("/pos/outlets", { params: { company_id: cid } }),
        client.get("/pos/stations", { params: { company_id: cid } }),
        client.get("/pos/terminals", { params: { company_id: cid } }),
        client.get("/catalog/menus", { params: { company_id: cid } }),
        client.get("/pos/sales", { params: { company_id: cid } }),
        client.get("/pos/warehouses", { params: { company_id: cid } }),
      ]);
      setOutlets(o.data); setStations(s.data); setTerminals(t.data); setMenus(m.data); setSales(v.data); setWarehouses(w.data);
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر تحميل بيانات POS"); }
  }
  useEffect(() => { void load(); }, [cid]);

  async function createOutlet(e: any) {
    e.preventDefault();
    try { await client.post("/pos/outlets", { company_id: cid, branch_id: Number(branchId), ...outletForm }); setOutletForm({ code: "", name: "", outlet_type: "restaurant" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل إنشاء المكان"); }
  }
  async function assignWarehouse(e: any) {
    e.preventDefault();
    try { await client.patch(`/pos/outlets/${selectedOutlet}/warehouse`, null, { params: { company_id: cid, warehouse_id: Number(outletWarehouseId) } }); setError(""); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل ربط مخزن الاستهلاك"); }
  }
  async function createStation(e: any) {
    e.preventDefault();
    try { await client.post("/pos/stations", { company_id: cid, branch_id: Number(branchId), outlet_id: Number(selectedOutlet) || null, ...stationForm }); setStationForm({ code: "", name: "", station_type: "kitchen" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل إنشاء محطة التحضير"); }
  }
  async function createTerminal(e: any) {
    e.preventDefault();
    try { await client.post("/pos/terminals", { company_id: cid, branch_id: Number(branchId), outlet_id: Number(selectedOutlet), ...terminalForm }); setTerminalForm({ code: "", name: "", device_identifier: "" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل إنشاء جهاز POS"); }
  }
  async function linkMenu(e: any) {
    e.preventDefault();
    try { await client.post("/pos/terminals/menus", { terminal_id: Number(selectedTerminal), menu_id: Number(selectedMenu), price_list_id: Number(priceListId) || null }, { params: { company_id: cid } }); setError(""); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل ربط المنيو بالجهاز"); }
  }
  async function routeItem(e: any) {
    e.preventDefault();
    try { await client.post("/pos/menu-routes", { terminal_id: Number(selectedTerminal), menu_item_id: Number(selectedMenuItem), station_id: Number(selectedStation) }, { params: { company_id: cid } }); setError(""); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل ربط صنف المنيو بالمحطة"); }
  }
  async function checkout(e: any) {
    e.preventDefault();
    if (!activeMenuItem) return setError("اختر صنفًا من المنيو");
    try {
      await client.post("/pos/checkout", {
        company_id: cid, partner_id: Number(partnerId), warehouse_id: Number(warehouseId),
        number: "POS-" + Date.now(), payment_date: new Date().toISOString().slice(0, 10),
        method, terminal_id: Number(selectedTerminal),
        lines: [{ menu_item_id: Number(selectedMenuItem), quantity: Number(qty) }],
      });
      setError(""); await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "فشل إتمام الطلب"); }
  }
  async function loadQueue() {
    if (!selectedStation) return;
    try { const r = await client.get(`/pos/stations/${selectedStation}/queue`, { params: { company_id: cid, status: "queued" } }); setQueue(r.data); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل تحميل شاشة المطبخ/البار"); }
  }
  async function move(routeId: number, status: string) {
    try { await client.patch(`/pos/order-routes/${routeId}`, { status }, { params: { company_id: cid } }); await loadQueue(); }
    catch (e: any) { setError(e?.response?.data?.detail || "فشل تحديث حالة الطلب"); }
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">Restaurant & Hotel POS</h1>
      <p className="text-sm text-muted-foreground">مكان الخدمة ← جهاز POS ← المنيو ← صنف المنيو ← محطة التحضير (مطبخ/بار) ← شاشة التنفيذ.</p>
    </header>
    {error && <div className="rounded-xl border bg-destructive/10 p-3">{error}</div>}
    <div className="flex gap-2">
      {([["sale","البيع"],["setup","إعداد الأماكن والأجهزة"],["kds","المطبخ / البار"]] as const).map(([k, label]) =>
        <button key={k} onClick={() => setTab(k)} className={`rounded-lg border px-4 py-2 ${tab === k ? "bg-primary text-primary-foreground" : ""}`}>{label}</button>
      )}
    </div>

    {tab === "setup" && <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={createOutlet} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">1. إضافة مكان خدمة</h2>
        <input required value={branchId} onChange={e => setBranchId(e.target.value)} placeholder="Branch ID" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={outletForm.code} onChange={e => setOutletForm({...outletForm,code:e.target.value})} placeholder="SEA-REST" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={outletForm.name} onChange={e => setOutletForm({...outletForm,name:e.target.value})} placeholder="مطعم البحر" className="w-full rounded-lg border px-3 py-2"/>
        <select value={outletForm.outlet_type} onChange={e => setOutletForm({...outletForm,outlet_type:e.target.value})} className="w-full rounded-lg border px-3 py-2"><option value="restaurant">Restaurant</option><option value="bar">Bar</option><option value="cafe">Cafe</option><option value="pool">Pool</option><option value="room_service">Room Service</option></select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">إضافة المكان</button>
      </form>
      <form onSubmit={assignWarehouse} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">ربط مخزن الاستهلاك بالمكان</h2>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name} — Warehouse {x.warehouse_id || "غير محدد"}</option>)}</select>
        <select required value={outletWarehouseId} onChange={e => setOutletWarehouseId(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المخزن الفرعي</option>{warehouses.filter(x => !x.is_central).map(x => <option key={x.id} value={x.id}>{x.name} — {x.code}</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">حفظ مخزن الاستهلاك</button>
      </form>
      </form>

      <form onSubmit={createStation} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">2. إضافة محطة إخراج</h2>
        <input required value={stationForm.code} onChange={e => setStationForm({...stationForm,code:e.target.value})} placeholder="SEA-KITCHEN" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={stationForm.name} onChange={e => setStationForm({...stationForm,name:e.target.value})} placeholder="مطبخ مطعم البحر" className="w-full rounded-lg border px-3 py-2"/>
        <select value={stationForm.station_type} onChange={e => setStationForm({...stationForm,station_type:e.target.value})} className="w-full rounded-lg border px-3 py-2"><option value="kitchen">Kitchen</option><option value="bar">Bar</option><option value="cold_kitchen">Cold Kitchen</option><option value="pastry">Pastry</option></select>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">إضافة المحطة وربطها بالمكان</button>
      </form>

      <form onSubmit={createTerminal} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">3. ربط جهاز POS بالمكان</h2>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <input required value={terminalForm.code} onChange={e => setTerminalForm({...terminalForm,code:e.target.value})} placeholder="SEA-POS-01" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={terminalForm.name} onChange={e => setTerminalForm({...terminalForm,name:e.target.value})} placeholder="POS مطعم البحر 1" className="w-full rounded-lg border px-3 py-2"/>
        <input value={terminalForm.device_identifier} onChange={e => setTerminalForm({...terminalForm,device_identifier:e.target.value})} placeholder="Device ID / Serial" className="w-full rounded-lg border px-3 py-2"/>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">إضافة الجهاز</button>
      </form>

      <form onSubmit={linkMenu} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">4. ربط المنيو والأسعار بالجهاز</h2>
        <select required value={selectedTerminal} onChange={e => setSelectedTerminal(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">الجهاز</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="w-full rounded-lg border px-3 py-2"><option value="">المنيو</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
        <input value={priceListId} onChange={e => setPriceListId(e.target.value)} placeholder="Price List ID (اختياري إذا كان سعر الصنف Override)" className="w-full rounded-lg border px-3 py-2"/>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">ربط المنيو</button>
      </form>

      <form onSubmit={routeItem} className="rounded-2xl border bg-card p-5 space-y-3 lg:col-span-2">
        <h2 className="font-bold">5. تحديد أين يخرج كل صنف</h2>
        <select required value={selectedTerminal} onChange={e => setSelectedTerminal(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">POS</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="rounded-lg border px-3 py-2"><option value="">Menu</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
        <select required value={selectedMenuItem} onChange={e => setSelectedMenuItem(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">Menu Item</option>{activeMenu?.items?.map((x:AnyRow) => <option key={x.id} value={x.id}>#{x.id} Product {x.product_id}</option>)}</select>
        <select required value={selectedStation} onChange={e => setSelectedStation(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">Station</option>{stations.map(x => <option key={x.id} value={x.id}>{x.name} ({x.station_type})</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">حفظ Routing</button>
      </form>
    </div>}

    {tab === "sale" && <div className="grid gap-4 lg:grid-cols-3">
      <form onSubmit={checkout} className="rounded-2xl border bg-card p-5 space-y-3 lg:col-span-2">
        <h2 className="font-bold">طلب من المنيو</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <input required value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="Customer/Partner ID" className="rounded-lg border px-3 py-2"/>
          <input required value={warehouseId} onChange={e => setWarehouseId(e.target.value)} placeholder="Warehouse ID" className="rounded-lg border px-3 py-2"/>
          <select required value={selectedTerminal} onChange={e => setSelectedTerminal(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">POS / المكان</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name} — Outlet {x.outlet_id}</option>)}</select>
          <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="rounded-lg border px-3 py-2"><option value="">Menu</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
          <select required value={selectedMenuItem} onChange={e => setSelectedMenuItem(e.target.value)} className="rounded-lg border px-3 py-2 md:col-span-2"><option value="">اختر من المنيو</option>{activeMenu?.items?.map((x:AnyRow) => <option key={x.id} value={x.id}>#{x.id} Product {x.product_id}{x.sale_price_override != null ? ` — ${x.sale_price_override}` : ""}</option>)}</select>
          <input required type="number" min="0.01" step="0.01" value={qty} onChange={e => setQty(e.target.value)} placeholder="الكمية" className="rounded-lg border px-3 py-2"/>
          <select value={method} onChange={e => setMethod(e.target.value)} className="rounded-lg border px-3 py-2"><option value="cash">Cash</option><option value="card">Card</option><option value="bank">Bank</option><option value="wallet">Wallet</option></select>
        </div>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">إرسال الطلب وتنفيذ البيع</button>
      </form>
      <div className="rounded-2xl border bg-card p-5"><h2 className="font-bold mb-3">الأجهزة</h2>{terminals.map(x => <div key={x.id} className="border-b py-2">{x.name}<div className="text-xs text-muted-foreground">{x.code} · Outlet {x.outlet_id}</div></div>)}</div>
      <div className="rounded-2xl border bg-card p-5 lg:col-span-3"><h2 className="font-bold mb-3">آخر مبيعات POS</h2>{sales.slice(0,20).map(x => <div key={x.id} className="flex justify-between border-b py-2"><span>{x.number}</span><span>{x.total} · {x.status}</span></div>)}</div>
    </div>}

    {tab === "kds" && <div className="space-y-4">
      <div className="rounded-2xl border bg-card p-5 flex gap-3">
        <select value={selectedStation} onChange={e => setSelectedStation(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">اختر المطبخ/البار</option>{stations.map(x => <option key={x.id} value={x.id}>{x.name} ({x.station_type})</option>)}</select>
        <button onClick={() => void loadQueue()} className="rounded-lg border px-4 py-2">تحديث الطابور</button>
      </div>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">{queue.map(x =>
        <div key={x.route_id} className="rounded-2xl border bg-card p-5">
          <div className="flex justify-between font-bold"><span>{x.order_number}</span><span>× {x.quantity}</span></div>
          <div className="mt-2 text-sm">Item #{x.item_id}</div>
          <div className="mt-4 flex gap-2"><button onClick={() => void move(x.route_id,"preparing")} className="rounded-lg border px-3 py-2">بدء</button><button onClick={() => void move(x.route_id,"ready")} className="rounded-lg border px-3 py-2">جاهز</button><button onClick={() => void move(x.route_id,"served")} className="rounded-lg bg-primary px-3 py-2 text-primary-foreground">تم التسليم</button></div>
        </div>
      )}</div>
    </div>}
  </section>;
}
