import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
type Carrier = { id: number; code: string; name: string; is_active: boolean };
type Method = { id: number; carrier_id: number; name: string; payment_method: string };

function companyId(): number | null {
  const value = Number(localStorage.getItem("company_id"));
  return Number.isInteger(value) && value > 0 ? value : null;
}
function errorText(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((x) => typeof x === "object" && x !== null && "msg" in x ? String((x as { msg: unknown }).msg) : String(x)).join("؛ ");
  return "تعذر تنفيذ العملية";
}
const inputClass = "w-full rounded-lg border bg-background px-3 py-2 text-sm";

export default function ShippingPage() {
  const cid = companyId();
  const [carriers, setCarriers] = useState<Carrier[]>([]);
  const [methods, setMethods] = useState<Method[]>([]);
  const [shipments, setShipments] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [carrierForm, setCarrierForm] = useState({ code: "", name: "", api_base_url: "", settlement_account_id: "", cash_account_id: "", fee_account_id: "", settlement_journal_id: "", branch_id: "" });
  const [methodForm, setMethodForm] = useState({ carrier_id: "", name: "", payment_method: "prepaid", payment_account_id: "", base_fee: "0", cod_fee_percent: "0", estimated_days: "1" });
  const [shipmentForm, setShipmentForm] = useState({ carrier_id: "", method_id: "", sales_document_id: "", tracking_no: "", cod_amount: "0", shipping_fee: "0", customer_name: "", phone: "", address: "", notes: "" });

  const load = useCallback(async () => {
    if (!cid) { setError("اختر شركة فعالة أولاً."); setLoading(false); return; }
    setLoading(true); setError("");
    try {
      const [c, s] = await Promise.all([client.get(`/shipping/carriers?company_id=${cid}`), client.get(`/shipping/shipments?company_id=${cid}`)]);
      const loaded = Array.isArray(c.data) ? c.data : [];
      setCarriers(loaded); setShipments(Array.isArray(s.data) ? s.data : []);
      if (loaded.length) {
        const id = Number(methodForm.carrier_id) || loaded[0].id;
        const m = await client.get(`/shipping/methods?carrier_id=${id}`);
        setMethods(Array.isArray(m.data) ? m.data : []);
      } else setMethods([]);
    } catch (e) { setError(errorText(e)); } finally { setLoading(false); }
  }, [cid, methodForm.carrier_id]);
  useEffect(() => { void load(); }, [load]);
  const selectedMethods = useMemo(() => methods.filter((m) => !shipmentForm.carrier_id || m.carrier_id === Number(shipmentForm.carrier_id)), [methods, shipmentForm.carrier_id]);

  async function loadMethods(id: string) {
    setMethodForm((v) => ({ ...v, carrier_id: id }));
    setShipmentForm((v) => ({ ...v, carrier_id: id, method_id: "" }));
    if (!id) return setMethods([]);
    try { const r = await client.get(`/shipping/methods?carrier_id=${Number(id)}`); setMethods(Array.isArray(r.data) ? r.data : []); }
    catch (e) { setError(errorText(e)); }
  }

  async function submitCarrier(e: FormEvent) {
    e.preventDefault(); if (!cid) return setError("اختر شركة فعالة أولاً.");
    if (!carrierForm.settlement_account_id || !carrierForm.cash_account_id || !carrierForm.fee_account_id) return setError("يجب تحديد حساب التسوية وحساب النقدية وحساب الرسوم لشركة الشحن.");
    if (!!carrierForm.settlement_journal_id !== !!carrierForm.branch_id) return setError("يجب تحديد دفتر التسوية والفرع معاً.");
    setSaving(true); setError("");
    try {
      await client.post("/shipping/carriers", { company_id: cid, code: carrierForm.code.trim(), name: carrierForm.name.trim(), api_base_url: carrierForm.api_base_url.trim() || null, settlement_account_id: Number(carrierForm.settlement_account_id), cash_account_id: Number(carrierForm.cash_account_id), fee_account_id: Number(carrierForm.fee_account_id), settlement_journal_id: carrierForm.settlement_journal_id ? Number(carrierForm.settlement_journal_id) : null, branch_id: carrierForm.branch_id ? Number(carrierForm.branch_id) : null });
      setCarrierForm({ code: "", name: "", api_base_url: "", settlement_account_id: "", cash_account_id: "", fee_account_id: "", settlement_journal_id: "", branch_id: "" }); await load();
    } catch (e) { setError(errorText(e)); } finally { setSaving(false); }
  }

  async function submitMethod(e: FormEvent) {
    e.preventDefault(); if (!methodForm.carrier_id) return setError("اختر شركة الشحن.");
    setSaving(true); setError("");
    try {
      await client.post("/shipping/methods", { carrier_id: Number(methodForm.carrier_id), name: methodForm.name.trim(), payment_method: methodForm.payment_method, payment_account_id: methodForm.payment_account_id ? Number(methodForm.payment_account_id) : null, base_fee: Number(methodForm.base_fee || 0), cod_fee_percent: Number(methodForm.cod_fee_percent || 0), estimated_days: Number(methodForm.estimated_days || 1) });
      setMethodForm((v) => ({ ...v, name: "", payment_account_id: "", base_fee: "0", cod_fee_percent: "0", estimated_days: "1" })); await loadMethods(methodForm.carrier_id);
    } catch (e) { setError(errorText(e)); } finally { setSaving(false); }
  }

  async function submitShipment(e: FormEvent) {
    e.preventDefault(); if (!cid) return setError("اختر شركة فعالة أولاً.");
    setSaving(true); setError("");
    try {
      await client.post("/shipping/shipments", { company_id: cid, carrier_id: Number(shipmentForm.carrier_id), method_id: Number(shipmentForm.method_id), sales_document_id: shipmentForm.sales_document_id ? Number(shipmentForm.sales_document_id) : null, tracking_no: shipmentForm.tracking_no.trim(), cod_amount: Number(shipmentForm.cod_amount || 0), shipping_fee: Number(shipmentForm.shipping_fee || 0), customer_name: shipmentForm.customer_name.trim(), phone: shipmentForm.phone.trim() || null, address: shipmentForm.address.trim() || null, notes: shipmentForm.notes.trim() || null });
      setShipmentForm((v) => ({ ...v, tracking_no: "", sales_document_id: "", cod_amount: "0", shipping_fee: "0", customer_name: "", phone: "", address: "", notes: "" })); await load();
    } catch (e) { setError(errorText(e)); } finally { setSaving(false); }
  }

  async function changeStatus(id: number, nextStatus: string) {
    if (!cid) return setError("اختر شركة فعالة أولاً.");
    setSaving(true); setError("");
    try { await client.post(`/shipping/shipments/${id}/status?company_id=${cid}&value=${encodeURIComponent(nextStatus)}`); await load(); }
    catch (e) { setError(errorText(e)); } finally { setSaving(false); }
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">الشحن والتوصيل</h1><p className="mt-1 text-sm text-muted-foreground">إدارة شركات الشحن وطرق الدفع والشحنات ودورة التتبع.</p></header>
    {error && <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
    <div className="grid gap-6 xl:grid-cols-3">
      <form onSubmit={submitCarrier} className="space-y-3 rounded-2xl border bg-card p-5"><h2 className="font-semibold">إضافة شركة شحن</h2><input className={inputClass} required placeholder="الكود" value={carrierForm.code} onChange={(e) => setCarrierForm({ ...carrierForm, code: e.target.value })}/><input className={inputClass} required placeholder="اسم الشركة" value={carrierForm.name} onChange={(e) => setCarrierForm({ ...carrierForm, name: e.target.value })}/><input className={inputClass} placeholder="API Base URL" value={carrierForm.api_base_url} onChange={(e) => setCarrierForm({ ...carrierForm, api_base_url: e.target.value })}/><input className={inputClass} required type="number" min="1" placeholder="حساب التسوية" value={carrierForm.settlement_account_id} onChange={(e) => setCarrierForm({ ...carrierForm, settlement_account_id: e.target.value })}/><input className={inputClass} required type="number" min="1" placeholder="حساب النقدية" value={carrierForm.cash_account_id} onChange={(e) => setCarrierForm({ ...carrierForm, cash_account_id: e.target.value })}/><input className={inputClass} required type="number" min="1" placeholder="حساب رسوم الشحن" value={carrierForm.fee_account_id} onChange={(e) => setCarrierForm({ ...carrierForm, fee_account_id: e.target.value })}/><div className="grid grid-cols-2 gap-3"><input className={inputClass} type="number" min="1" placeholder="دفتر التسوية" value={carrierForm.settlement_journal_id} onChange={(e) => setCarrierForm({ ...carrierForm, settlement_journal_id: e.target.value })}/><input className={inputClass} type="number" min="1" placeholder="الفرع" value={carrierForm.branch_id} onChange={(e) => setCarrierForm({ ...carrierForm, branch_id: e.target.value })}/></div><button disabled={saving || !cid} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">حفظ الشركة</button></form>
      <form onSubmit={submitMethod} className="space-y-3 rounded-2xl border bg-card p-5"><h2 className="font-semibold">إضافة طريقة شحن</h2><select className={inputClass} required value={methodForm.carrier_id} onChange={(e) => void loadMethods(e.target.value)}><option value="">اختر شركة</option>{carriers.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}</select><input className={inputClass} required placeholder="اسم الطريقة" value={methodForm.name} onChange={(e) => setMethodForm({ ...methodForm, name: e.target.value })}/><select className={inputClass} value={methodForm.payment_method} onChange={(e) => setMethodForm({ ...methodForm, payment_method: e.target.value })}><option value="prepaid">مدفوع مسبقاً</option><option value="cod">الدفع عند الاستلام</option><option value="mixed">مختلط</option></select><input className={inputClass} type="number" min="1" placeholder="حساب الدفع (اختياري)" value={methodForm.payment_account_id} onChange={(e) => setMethodForm({ ...methodForm, payment_account_id: e.target.value })}/><input className={inputClass} type="number" min="0" step="0.01" placeholder="الرسوم الأساسية" value={methodForm.base_fee} onChange={(e) => setMethodForm({ ...methodForm, base_fee: e.target.value })}/><input className={inputClass} type="number" min="0" max="100" step="0.01" placeholder="COD %" value={methodForm.cod_fee_percent} onChange={(e) => setMethodForm({ ...methodForm, cod_fee_percent: e.target.value })}/><input className={inputClass} type="number" min="1" placeholder="الأيام المتوقعة" value={methodForm.estimated_days} onChange={(e) => setMethodForm({ ...methodForm, estimated_days: e.target.value })}/><button disabled={saving || !cid} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">حفظ الطريقة</button></form>
      <form onSubmit={submitShipment} className="space-y-3 rounded-2xl border bg-card p-5"><h2 className="font-semibold">إنشاء شحنة</h2><select className={inputClass} required value={shipmentForm.carrier_id} onChange={(e) => { setShipmentForm({ ...shipmentForm, carrier_id: e.target.value, method_id: "" }); void loadMethods(e.target.value); }}><option value="">اختر شركة</option>{carriers.map((c) => <option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}</select><select className={inputClass} required value={shipmentForm.method_id} onChange={(e) => setShipmentForm({ ...shipmentForm, method_id: e.target.value })}><option value="">اختر الطريقة</option>{selectedMethods.map((m) => <option key={m.id} value={m.id}>{m.name} — {m.payment_method}</option>)}</select><input className={inputClass} required placeholder="رقم التتبع" value={shipmentForm.tracking_no} onChange={(e) => setShipmentForm({ ...shipmentForm, tracking_no: e.target.value })}/><input className={inputClass} type="number" min="1" placeholder="رقم مستند المبيعات (اختياري)" value={shipmentForm.sales_document_id} onChange={(e) => setShipmentForm({ ...shipmentForm, sales_document_id: e.target.value })}/><input className={inputClass} required placeholder="اسم العميل" value={shipmentForm.customer_name} onChange={(e) => setShipmentForm({ ...shipmentForm, customer_name: e.target.value })}/><input className={inputClass} placeholder="الهاتف" value={shipmentForm.phone} onChange={(e) => setShipmentForm({ ...shipmentForm, phone: e.target.value })}/><input className={inputClass} placeholder="العنوان" value={shipmentForm.address} onChange={(e) => setShipmentForm({ ...shipmentForm, address: e.target.value })}/><div className="grid grid-cols-2 gap-3"><input className={inputClass} type="number" min="0" step="0.01" placeholder="COD" value={shipmentForm.cod_amount} onChange={(e) => setShipmentForm({ ...shipmentForm, cod_amount: e.target.value })}/><input className={inputClass} type="number" min="0" step="0.01" placeholder="رسوم الشحن" value={shipmentForm.shipping_fee} onChange={(e) => setShipmentForm({ ...shipmentForm, shipping_fee: e.target.value })}/></div><textarea className={inputClass} placeholder="ملاحظات" value={shipmentForm.notes} onChange={(e) => setShipmentForm({ ...shipmentForm, notes: e.target.value })}/><button disabled={saving || !cid} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">إنشاء الشحنة</button></form>
    </div>
    <div className="overflow-hidden rounded-2xl border bg-card"><div className="flex items-center justify-between border-b p-4"><div><h2 className="font-semibold">الشحنات</h2><p className="text-xs text-muted-foreground">{shipments.length} شحنة</p></div><button type="button" onClick={() => void load()} disabled={loading} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>{loading ? <div className="p-8 text-center">جارٍ التحميل...</div> : shipments.length === 0 ? <div className="p-8 text-center text-muted-foreground">لا توجد شحنات.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40"><th className="p-3 text-right">التتبع</th><th className="p-3 text-right">العميل</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">COD</th><th className="p-3 text-right">الإجراء</th></tr></thead><tbody>{shipments.map((row, i) => { const status = String(row.status ?? "pending"); const next: Record<string,string> = { pending:"picked_up", picked_up:"in_transit", in_transit:"out_for_delivery", out_for_delivery:"delivered", delivered:"returned" }; return <tr key={String(row.id ?? i)} className="border-b last:border-0"><td className="p-3 font-mono">{String(row.tracking_no ?? "—")}</td><td className="p-3">{String(row.customer_name ?? "—")}</td><td className="p-3">{status}</td><td className="p-3">{String(row.cod_amount ?? "0")}</td><td className="p-3">{next[status] ? <button disabled={saving} type="button" onClick={() => void changeStatus(Number(row.id), next[status])} className="rounded-lg border px-3 py-1.5 text-xs">{next[status]}</button> : "—"}</td></tr>; })}</tbody></table></div>}</div>
  </section>;
}
