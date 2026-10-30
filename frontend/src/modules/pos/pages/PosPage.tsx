import { useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { useCompanyClockDate } from "@/utils/format-date";
import client from "@/shared/api/client";
import { cachePosData, enqueueCheckout, getDeviceId, installOfflineSync, listCheckoutQueue, readPosCache, type PosCheckoutPayload } from "../services/offlinePos";

type AnyRow = Record<string, any>;
const companyId = () => Number(localStorage.getItem("company_id")) || 0;

export default function PosPage() {
  const { t, i18n } = useTranslation();
  const cid = companyId();
  const { companyDate, error: clockError } = useCompanyClockDate(cid);
  const [outlets, setOutlets] = useState<AnyRow[]>([]);
  const [stations, setStations] = useState<AnyRow[]>([]);
  const [terminals, setTerminals] = useState<AnyRow[]>([]);
  const [menus, setMenus] = useState<AnyRow[]>([]);
  const [sales, setSales] = useState<AnyRow[]>([]);
  const [warehouses, setWarehouses] = useState<AnyRow[]>([]);
  const [queue, setQueue] = useState<AnyRow[]>([]);
  const [offlineQueue, setOfflineQueue] = useState<any[]>([]);
  const [online, setOnline] = useState(navigator.onLine);
  const [error, setError] = useState("");
  const [branchId, setBranchId] = useState("");
  const [selectedOutlet, setSelectedOutlet] = useState("");
  const [selectedTerminal, setSelectedTerminal] = useState("");
  const [cashierShift, setCashierShift] = useState<AnyRow | null>(null);
  const [openingCash, setOpeningCash] = useState("0");
  const [countedCash, setCountedCash] = useState("");
  const [selectedStation, setSelectedStation] = useState("");
  const [selectedMenu, setSelectedMenu] = useState("");
  const [selectedMenuItem, setSelectedMenuItem] = useState("");
  const [partnerId, setPartnerId] = useState("");
  const [warehouseId, setWarehouseId] = useState("");
  const [qty, setQty] = useState("1.0");
  const [method, setMethod] = useState("cash");
  const [tab, setTab] = useState<"sale" | "setup" | "kds">("sale");

  const [outletForm, setOutletForm] = useState({ code: "", name: "", outlet_type: "restaurant" });
  const [stationForm, setStationForm] = useState({ code: "", name: "", station_type: "kitchen" });
  const [terminalForm, setTerminalForm] = useState({ code: "", name: "", device_identifier: "" });
  const [priceListId, setPriceListId] = useState("");
  const [outletWarehouseId, setOutletWarehouseId] = useState("");

  const activeMenu = useMemo(() => menus.find(x => String(x.id) === selectedMenu), [menus, selectedMenu]);
  const activeMenuItem = useMemo(() => activeMenu?.items?.find((x: AnyRow) => String(x.id) === selectedMenuItem), [activeMenu, selectedMenuItem]);
  const activeTerminal = useMemo(() => terminals.find(x => String(x.id) === selectedTerminal), [terminals, selectedTerminal]);
  const activeOutlet = useMemo(() => outlets.find(x => String(x.id) === String(activeTerminal?.outlet_id)), [outlets, activeTerminal]);

  async function refreshOfflineQueue() {
    setOfflineQueue(await listCheckoutQueue());
  }

  useEffect(() => {
    const onOnline = () => setOnline(true);
    const onOffline = () => setOnline(false);
    window.addEventListener("online", onOnline);
    window.addEventListener("offline", onOffline);
    const cleanup = installOfflineSync(() => { void refreshOfflineQueue(); });
    void refreshOfflineQueue();
    return () => { window.removeEventListener("online", onOnline); window.removeEventListener("offline", onOffline); cleanup(); };
  }, []);

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
      await Promise.all([
        cachePosData(`company:${cid}:outlets`, o.data), cachePosData(`company:${cid}:stations`, s.data),
        cachePosData(`company:${cid}:terminals`, t.data), cachePosData(`company:${cid}:menus`, m.data),
        cachePosData(`company:${cid}:sales`, v.data), cachePosData(`company:${cid}:warehouses`, w.data),
      ]);
    } catch (e: any) {
      const [o,s,t,m,v,w] = await Promise.all([
        readPosCache<AnyRow[]>(`company:${cid}:outlets`), readPosCache<AnyRow[]>(`company:${cid}:stations`),
        readPosCache<AnyRow[]>(`company:${cid}:terminals`), readPosCache<AnyRow[]>(`company:${cid}:menus`),
        readPosCache<AnyRow[]>(`company:${cid}:sales`), readPosCache<AnyRow[]>(`company:${cid}:warehouses`),
      ]);
      if (o) setOutlets(o); if (s) setStations(s); if (t) setTerminals(t); if (m) setMenus(m); if (v) setSales(v); if (w) setWarehouses(w);
      setError("{t("pos.offlineCacheNotice")}");
    }
  }
  useEffect(() => { void load(); }, [cid]);
  useEffect(() => {
    setCashierShift(null);
    if (!cid || !selectedTerminal) return;
    client.get("/pos/shifts/current", { params: { company_id: cid, terminal_id: Number(selectedTerminal) } })
      .then(({ data }) => setCashierShift(data))
      .catch((e: any) => setError(e?.response?.data?.detail || "{t("pos.loadShiftFailed")}"));
  }, [cid, selectedTerminal]);

  async function createOutlet(e: any) {
    e.preventDefault();
    try { await client.post("/pos/outlets", { company_id: cid, branch_id: Number(branchId), ...outletForm }); setOutletForm({ code: "", name: "", outlet_type: "restaurant" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.createOutletFailed")}"); }
  }
  async function assignWarehouse(e: any) {
    e.preventDefault();
    try { await client.patch(`/pos/outlets/${selectedOutlet}/warehouse`, null, { params: { company_id: cid, warehouse_id: Number(outletWarehouseId) } }); setError(""); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.assignWarehouseFailed")}"); }
  }
  async function createStation(e: any) {
    e.preventDefault();
    try { await client.post("/pos/stations", { company_id: cid, branch_id: Number(branchId), outlet_id: Number(selectedOutlet) || null, ...stationForm }); setStationForm({ code: "", name: "", station_type: "kitchen" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.createStationFailed")}"); }
  }
  async function createTerminal(e: any) {
    e.preventDefault();
    try { await client.post("/pos/terminals", { company_id: cid, branch_id: Number(branchId), outlet_id: Number(selectedOutlet), ...terminalForm }); setTerminalForm({ code: "", name: "", device_identifier: "" }); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.createTerminalFailed")}"); }
  }
  async function linkMenu(e: any) {
    e.preventDefault();
    try { await client.post("/pos/terminals/menus", { terminal_id: Number(selectedTerminal), menu_id: Number(selectedMenu), price_list_id: Number(priceListId) || null }, { params: { company_id: cid } }); setError(""); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.linkMenuFailed")}"); }
  }
  async function routeItem(e: any) {
    e.preventDefault();
    try { await client.post("/pos/menu-routes", { terminal_id: Number(selectedTerminal), menu_item_id: Number(selectedMenuItem), station_id: Number(selectedStation) }, { params: { company_id: cid } }); setError(""); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.routeItemFailed")}"); }
  }
  async function openCashierShift() {
    if (!selectedTerminal) return setError("{t("pos.selectTerminal")}");
    try {
      const { data } = await client.post("/pos/shifts/open", {
        company_id: cid, terminal_id: Number(selectedTerminal), opening_cash: Number(openingCash || 0),
      });
      setCashierShift(data); setCountedCash(""); setError("");
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.openShiftFailed")}"); }
  }
  async function closeCashierShift() {
    if (!cashierShift || !countedCash) return setError("{t("pos.enterCountedCash")}");
    if (offlineQueue.length) return setError("{t("pos.syncBeforeClose")}");
    try {
      const { data } = await client.post(`/pos/shifts/${cashierShift.id}/close`, { counted_cash: Number(countedCash) }, { params: { company_id: cid } });
      setCashierShift(data); setError("");
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.closeShiftFailed")}"); }
  }
  async function checkout(e: any) {
    e.preventDefault();
    if (!companyDate) return setError(clockError || "{t("pos.companyDateRequired")}");
    if (!activeMenuItem) return setError("{t("pos.selectMenuItem")}");
    try {
      const payload: PosCheckoutPayload = {
        company_id: cid, partner_id: Number(partnerId), warehouse_id: Number(warehouseId),
        number: `POS-${getDeviceId().slice(0, 8)}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        payment_date: companyDate, method, terminal_id: Number(selectedTerminal),
        lines: [{ menu_item_id: Number(selectedMenuItem), quantity: Number(qty) }],
      };
      if (!navigator.onLine) {
        await enqueueCheckout(payload); await refreshOfflineQueue();
        setError("{t("pos.savedOffline")}");
      } else {
        try { await client.post("/pos/checkout", payload); setError(""); await load(); }
        catch (error: any) {
          if (!error?.response) {
            await enqueueCheckout(payload); await refreshOfflineQueue();
            setError("{t("pos.connectionSavedOffline")}");
          } else throw error;
        }
      }
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.checkoutFailed")}"); }
  }
  async function loadQueue() {
    if (!selectedStation) return;
    try { const r = await client.get(`/pos/stations/${selectedStation}/queue`, { params: { company_id: cid, status: "queued" } }); setQueue(r.data); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.loadKdsFailed")}"); }
  }
  async function move(routeId: number, status: string) {
    try { await client.patch(`/pos/order-routes/${routeId}`, { status }, { params: { company_id: cid } }); await loadQueue(); }
    catch (e: any) { setError(e?.response?.data?.detail || "{t("pos.updateOrderFailed")}"); }
  }

  return <section className="space-y-6 p-6" dir={i18n.dir()}>
    <header>
      <div className="mb-3 flex flex-wrap items-center gap-2"><span className={online ? "rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold text-emerald-700" : "rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800"}>{online ? t("pos.online") : t("pos.offline")}</span>{offlineQueue.length > 0 && <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-semibold text-blue-800">{offlineQueue.length} {t("pos.pendingSync")}</span>}</div>
      <h1 className="text-2xl font-bold">{t("pos.title")}</h1>
      <p className="text-sm text-muted-foreground">{t("pos.flowDescription")}</p>
    </header>
    {error && <div className="rounded-xl border bg-destructive/10 p-3">{error}</div>}
    <div className="flex gap-2">
      {([["sale","{t("pos.tabs.sale")}"],["setup","{t("pos.tabs.setup")}"],["kds","{t("pos.tabs.kds")}"]] as const).map(([k, label]) =>
        <button key={k} onClick={() => setTab(k)} className={`rounded-lg border px-4 py-2 ${tab === k ? "bg-primary text-primary-foreground" : ""}`}>{label}</button>
      )}
    </div>

    {tab === "setup" && <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={createOutlet} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">1. {t("pos.createOutlet")}</h2>
        <input required value={branchId} onChange={e => setBranchId(e.target.value)} placeholder="Branch ID" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={outletForm.code} onChange={e => setOutletForm({...outletForm,code:e.target.value})} placeholder="SEA-REST" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={outletForm.name} onChange={e => setOutletForm({...outletForm,name:e.target.value})} placeholder="مطعم البحر" className="w-full rounded-lg border px-3 py-2"/>
        <select value={outletForm.outlet_type} onChange={e => setOutletForm({...outletForm,outlet_type:e.target.value})} className="w-full rounded-lg border px-3 py-2"><option value="restaurant">Restaurant</option><option value="bar">Bar</option><option value="cafe">Cafe</option><option value="pool">Pool</option><option value="room_service">Room Service</option></select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.addOutlet")}</button>
      </form>
      <form onSubmit={assignWarehouse} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">{t("pos.assignWarehouse")}</h2>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name} — Warehouse {x.warehouse_id || "غير محدد"}</option>)}</select>
        <select required value={outletWarehouseId} onChange={e => setOutletWarehouseId(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المخزن الفرعي</option>{warehouses.filter(x => !x.is_central).map(x => <option key={x.id} value={x.id}>{x.name} — {x.code}</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.saveWarehouse")}</button>
      </form>

      <form onSubmit={createStation} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">2. {t("pos.createStation")}</h2>
        <input required value={stationForm.code} onChange={e => setStationForm({...stationForm,code:e.target.value})} placeholder="SEA-KITCHEN" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={stationForm.name} onChange={e => setStationForm({...stationForm,name:e.target.value})} placeholder="مطبخ مطعم البحر" className="w-full rounded-lg border px-3 py-2"/>
        <select value={stationForm.station_type} onChange={e => setStationForm({...stationForm,station_type:e.target.value})} className="w-full rounded-lg border px-3 py-2"><option value="kitchen">Kitchen</option><option value="bar">Bar</option><option value="cold_kitchen">Cold Kitchen</option><option value="pastry">Pastry</option></select>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.addStation")}</button>
      </form>

      <form onSubmit={createTerminal} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">3. {t("pos.createTerminal")}</h2>
        <select required value={selectedOutlet} onChange={e => setSelectedOutlet(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">اختر المكان</option>{outlets.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <input required value={terminalForm.code} onChange={e => setTerminalForm({...terminalForm,code:e.target.value})} placeholder="SEA-POS-01" className="w-full rounded-lg border px-3 py-2"/>
        <input required value={terminalForm.name} onChange={e => setTerminalForm({...terminalForm,name:e.target.value})} placeholder="POS مطعم البحر 1" className="w-full rounded-lg border px-3 py-2"/>
        <input value={terminalForm.device_identifier} onChange={e => setTerminalForm({...terminalForm,device_identifier:e.target.value})} placeholder="Device ID / Serial" className="w-full rounded-lg border px-3 py-2"/>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.addTerminal")}</button>
      </form>

      <form onSubmit={linkMenu} className="rounded-2xl border bg-card p-5 space-y-3">
        <h2 className="font-bold">4. {t("pos.linkMenu")}</h2>
        <select required value={selectedTerminal} onChange={e => setSelectedTerminal(e.target.value)} className="w-full rounded-lg border px-3 py-2"><option value="">الجهاز</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="w-full rounded-lg border px-3 py-2"><option value="">المنيو</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
        <input value={priceListId} onChange={e => setPriceListId(e.target.value)} placeholder="Price List ID (اختياري إذا كان سعر الصنف Override)" className="w-full rounded-lg border px-3 py-2"/>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.saveMenuLink")}</button>
      </form>

      <form onSubmit={routeItem} className="rounded-2xl border bg-card p-5 space-y-3 lg:col-span-2">
        <h2 className="font-bold">5. {t("pos.routeItem")}</h2>
        <select required value={selectedTerminal} onChange={e => setSelectedTerminal(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">POS</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name}</option>)}</select>
        <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="rounded-lg border px-3 py-2"><option value="">Menu</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
        <select required value={selectedMenuItem} onChange={e => setSelectedMenuItem(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">Menu Item</option>{activeMenu?.items?.map((x:AnyRow) => <option key={x.id} value={x.id}>#{x.id} Product {x.product_id}</option>)}</select>
        <select required value={selectedStation} onChange={e => setSelectedStation(e.target.value)} className="rounded-lg border px-3 py-2"><option value="">Station</option>{stations.map(x => <option key={x.id} value={x.id}>{x.name} ({x.station_type})</option>)}</select>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.saveRouting")}</button>
      </form>
    </div>}

    {tab === "sale" && <div className="grid gap-4 lg:grid-cols-3">
      <div className="rounded-2xl border bg-card p-5 lg:col-span-3">
        <h2 className="mb-3 font-bold">{t("pos.cashierShift")}</h2>
        {!selectedTerminal && <p className="text-sm text-muted-foreground">{t("pos.selectTerminalHint")}</p>}
        {selectedTerminal && !cashierShift && <div className="flex flex-wrap items-end gap-3">
          <label className="grid gap-1 text-sm">{t("pos.openingCash")}
            <input type="number" min="0" step="0.01" value={openingCash} onChange={e => setOpeningCash(e.target.value)} className="rounded-lg border px-3 py-2"/>
          </label>
          <button type="button" onClick={() => void openCashierShift()} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{t("pos.openShift")}</button>
        </div>}
        {cashierShift?.status === "open" && <div className="flex flex-wrap items-end gap-3">
          <div className="text-sm">الوردية #{cashierShift.id} مفتوحة · رصيد البداية {cashierShift.opening_cash}</div>
          <label className="grid gap-1 text-sm">{t("pos.countedCash")}
            <input type="number" min="0" step="0.01" value={countedCash} onChange={e => setCountedCash(e.target.value)} className="rounded-lg border px-3 py-2"/>
          </label>
          <button type="button" disabled={offlineQueue.length > 0} onClick={() => void closeCashierShift()} className="rounded-lg border px-4 py-2 disabled:opacity-50">إغلاق وتسوية الوردية</button>
          {offlineQueue.length > 0 && <span className="text-xs text-amber-700">لا يمكن الإغلاق مع طلبات غير متزامنة.</span>}
        </div>}
        {cashierShift?.status === "closed" && <div className="space-y-1 text-sm">
          <p>الوردية #{cashierShift.id} أُغلقت.</p>
          <p>المتوقع نقدًا: {cashierShift.expected_cash} · المعدود: {cashierShift.counted_cash} · الفرق: {cashierShift.variance}</p>
          <button type="button" onClick={() => void openCashierShift()} className="rounded-lg border px-4 py-2">{t("pos.openShift")} جديدة</button>
        </div>}
      </div>
      <form onSubmit={checkout} className="rounded-2xl border bg-card p-5 space-y-3 lg:col-span-2">
        <h2 className="font-bold">طلب من المنيو</h2>
        <div className="grid gap-3 md:grid-cols-2">
          <input required value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="Customer/Partner ID" className="rounded-lg border px-3 py-2"/>
          <input required value={warehouseId || (activeOutlet?.warehouse_id ? String(activeOutlet.warehouse_id) : "")} readOnly placeholder="Consumption Warehouse (auto from outlet)" className="rounded-lg border bg-muted px-3 py-2"/>
          <select required value={selectedTerminal} onChange={e => { const id=e.target.value; setSelectedTerminal(id); const terminal=terminals.find(x=>String(x.id)===id); const outlet=outlets.find(x=>String(x.id)===String(terminal?.outlet_id)); setWarehouseId(outlet?.warehouse_id ? String(outlet.warehouse_id) : ""); }} className="rounded-lg border px-3 py-2"><option value="">POS / المكان</option>{terminals.map(x => <option key={x.id} value={x.id}>{x.name} — Outlet {x.outlet_id}</option>)}</select>
          <select required value={selectedMenu} onChange={e => {setSelectedMenu(e.target.value);setSelectedMenuItem("")}} className="rounded-lg border px-3 py-2"><option value="">Menu</option>{menus.map(x => <option key={x.id} value={x.id}>{x.name_ar}</option>)}</select>
          <select required value={selectedMenuItem} onChange={e => setSelectedMenuItem(e.target.value)} className="rounded-lg border px-3 py-2 md:col-span-2"><option value="">اختر من المنيو</option>{activeMenu?.items?.map((x:AnyRow) => <option key={x.id} value={x.id}>#{x.id} Product {x.product_id}{x.sale_price_override != null ? ` — ${x.sale_price_override}` : ""}</option>)}</select>
          <input required type="number" min="0.01" step="0.01" value={qty} onChange={e => setQty(e.target.value)} placeholder="الكمية" className="rounded-lg border px-3 py-2"/>
          <select value={method} onChange={e => setMethod(e.target.value)} className="rounded-lg border px-3 py-2"><option value="cash">Cash</option><option value="card">Card</option><option value="bank">Bank</option><option value="wallet">Wallet</option></select>
        </div>
        <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">إرسال الطلب وتنفيذ {t("pos.tabs.sale")}</button>
      </form>
      <div className="rounded-2xl border bg-card p-5"><h2 className="font-bold mb-3">الأجهزة</h2>{terminals.map(x => <div key={x.id} className="border-b py-2">{x.name}<div className="text-xs text-muted-foreground">{x.code} · Outlet {x.outlet_id}</div></div>)}</div>
      <div className="rounded-2xl border bg-card p-5 lg:col-span-3"><h2 className="font-bold mb-3">آخر مبيعات POS</h2>{offlineQueue.map(x => <div key={x.id} className="flex justify-between border-b py-2"><span>{x.payload.number}</span><span>محفوظ محليًا · في انتظار المزامنة</span></div>)}{sales.slice(0,20).map(x => <div key={x.id} className="flex justify-between border-b py-2"><span>{x.number}</span><span>{x.total} · {x.status}</span></div>)}</div>
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
