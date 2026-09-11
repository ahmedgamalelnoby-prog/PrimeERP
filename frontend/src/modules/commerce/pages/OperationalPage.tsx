import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
const config: Record<string, { title: string; endpoint: string; kind: "partners" | "documents" | "shipping" }> = {
  "/customers": { title: "العملاء والموردون", endpoint: "/commerce/partners", kind: "partners" },
  "/sales/quotations": { title: "عروض المبيعات", endpoint: "/commerce/sales/documents", kind: "documents" },
  "/sales/orders": { title: "طلبات المبيعات", endpoint: "/commerce/sales/documents", kind: "documents" },
  "/purchases/orders": { title: "طلبات المشتريات", endpoint: "/commerce/purchases/documents", kind: "documents" },
  "/shipping": { title: "الشحن واللوجستيات", endpoint: "/shipping/carriers", kind: "shipping" },
};

function selectedCompanyId(): number | null {
  const raw = localStorage.getItem("company_id");
  if (!raw) return null;
  const value = Number(raw);
  return Number.isInteger(value) && value > 0 ? value : null;
}

export default function OperationalPage() {
  const path = useLocation().pathname;
  const meta = config[path] || config["/customers"];
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [partnerId, setPartnerId] = useState("");
  const [itemId, setItemId] = useState("");
  const [number, setNumber] = useState("");
  const [type, setType] = useState(path.startsWith("/purchases") ? "order" : path.includes("quotations") ? "quotation" : "order");
  const [amount, setAmount] = useState("");
  const companyId = selectedCompanyId();
  const query = useMemo(() => companyId ? `?company_id=${companyId}` : "", [companyId]);

  async function load() {
    setLoading(true);
    setError("");
    if (!companyId) {
      setRows([]);
      setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية تلقائياً.");
      setLoading(false);
      return;
    }
    try {
      const r = await client.get(`${meta.endpoint}${query}`);
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [meta.endpoint, query]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!companyId) {
      setError("لا يمكن الحفظ بدون شركة فعالة.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      if (meta.kind === "partners") {
        await client.post("/commerce/partners", { company_id: companyId, code, name, partner_type: "customer" });
      } else if (meta.kind === "documents") {
        await client.post(meta.endpoint, {
          company_id: companyId,
          partner_id: Number(partnerId),
          document_type: type,
          number,
          document_date: new Date().toISOString().slice(0, 10),
          lines: [{ item_id: Number(itemId), description: name, quantity: 1, unit_price: Number(amount || 0) }],
        });
      } else {
        await client.post("/shipping/carriers", { company_id: companyId, code, name });
      }
      setName(""); setCode(""); setPartnerId(""); setItemId(""); setNumber(""); setAmount("");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر حفظ السجل");
    } finally {
      setSaving(false);
    }
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">{meta.title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">واجهة تشغيل مرتبطة مباشرة بالـ API مع عزل الشركة والـ tenant.</p>
    </header>
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="font-semibold">إضافة سجل</h2>
        <input required value={code} onChange={e => setCode(e.target.value)} placeholder={meta.kind === "documents" ? "اختصار/مرجع" : "الكود"} className="w-full rounded-lg border bg-background px-3 py-2" />
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="الاسم / الوصف" className="w-full rounded-lg border bg-background px-3 py-2" />
        {meta.kind === "documents" && <>
          <input required type="number" min="1" value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="Partner ID" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required type="number" min="1" value={itemId} onChange={e => setItemId(e.target.value)} placeholder="Item ID" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required value={number} onChange={e => setNumber(e.target.value)} placeholder="رقم المستند" className="w-full rounded-lg border bg-background px-3 py-2" />
          <select value={type} onChange={e => setType(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2">
            <option value="quotation">Quotation</option><option value="order">Order</option><option value="delivery">Delivery</option><option value="invoice">Invoice</option><option value="credit_note">Credit Note</option><option value="requisition">Requisition</option><option value="rfq">RFQ</option><option value="receipt">Receipt</option><option value="bill">Bill</option><option value="debit_note">Debit Note</option>
          </select>
          <input required type="number" min="0" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="سعر الوحدة" className="w-full rounded-lg border bg-background px-3 py-2" />
        </>}
        {error && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button disabled={saving || !companyId} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "حفظ"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4"><h2 className="font-semibold">السجلات</h2><button onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-8 text-center text-sm text-muted-foreground">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">لا توجد سجلات.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40">{Object.keys(rows[0]).slice(0, 8).map(k => <th key={k} className="whitespace-nowrap px-4 py-3 text-right font-semibold">{k}</th>)}</tr></thead><tbody>{rows.map((r, i) => <tr key={String(r.id ?? i)} className="border-b last:border-0">{Object.keys(rows[0]).slice(0, 8).map(k => <td key={k} className="whitespace-nowrap px-4 py-3">{String(r[k] ?? "—")}</td>)}</tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
