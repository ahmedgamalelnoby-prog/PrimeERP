import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";
import { formatCompanyDate, getCompanyDateFormat, getLocalISODate, isCompanyDateFormat, setCompanyDateFormat, type CompanyDateFormat } from "@/utils/format-date";

type Row = Record<string, unknown>;
type RouteConfig = { title: string; endpoint: string; kind: "partners" | "documents" | "shipping"; partnerType?: "customer" | "vendor"; documentKind?: "sale" | "purchase"; documentType?: string };
const config: Record<string, RouteConfig> = {
  "/customers": { title: "العملاء", endpoint: "/commerce/partners", kind: "partners", partnerType: "customer" },
  "/purchasing/suppliers": { title: "الموردون", endpoint: "/commerce/partners", kind: "partners", partnerType: "vendor" },
  "/sales/quotations": { title: "عروض المبيعات", endpoint: "/commerce/sales/documents", kind: "documents", documentKind: "sale", documentType: "quotation" },
  "/sales/orders": { title: "طلبات المبيعات", endpoint: "/commerce/sales/documents", kind: "documents", documentKind: "sale", documentType: "order" },
  "/sales/invoices": { title: "فواتير المبيعات", endpoint: "/commerce/sales/documents", kind: "documents", documentKind: "sale", documentType: "invoice" },
  "/purchases/orders": { title: "طلبات المشتريات", endpoint: "/commerce/purchases/documents", kind: "documents", documentKind: "purchase", documentType: "order" },
  "/purchasing/invoices": { title: "فواتير المشتريات", endpoint: "/commerce/purchases/documents", kind: "documents", documentKind: "purchase", documentType: "bill" },
  "/shipping": { title: "الشحن واللوجستيات", endpoint: "/shipping/carriers", kind: "shipping" },
};

function selectedCompanyId(): number | null {
  try {
    const raw = localStorage.getItem("company_id");
    if (!raw) return null;
    const value = Number(raw);
    return Number.isInteger(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
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
  const [sourceOrderId, setSourceOrderId] = useState("");
  const [sourceLineId, setSourceLineId] = useState("");
  const [receiptIds, setReceiptIds] = useState("");
  const [type, setType] = useState(path === "/sales/invoices" ? "invoice" : path === "/purchasing/invoices" ? "bill" : path.startsWith("/purchases") ? "order" : path.includes("quotations") ? "quotation" : "order");
  const [amount, setAmount] = useState("");
  const [paymentAmount, setPaymentAmount] = useState("");
  const [paymentMethod, setPaymentMethod] = useState("bank");
  const [chequeNumber, setChequeNumber] = useState("");
  const [chequeBank, setChequeBank] = useState("");
  const [chequeDueDate, setChequeDueDate] = useState(getLocalISODate());
  const [payments, setPayments] = useState<Row[]>([]);
  const [dateFormat, setDateFormat] = useState<CompanyDateFormat>(() => getCompanyDateFormat(selectedCompanyId()));
  const companyId = selectedCompanyId();
  const query = useMemo(() => companyId ? `?company_id=${companyId}` : "", [companyId]);
  const isSale = meta.endpoint === "/commerce/sales/documents";
  const isPurchase = meta.endpoint === "/commerce/purchases/documents";
  const allowedDocumentTypes = isSale ? (meta.documentType ? [meta.documentType] : ["quotation","order","delivery","invoice","credit_note"]) : ["requisition","rfq","order","receipt","bill","debit_note"];

  async function actionDocument(id: number, action: string) {
    if (!companyId) return;
    setError("");
    try {
      const prefix = isSale ? "sales" : isPurchase ? "purchases" : null;
      if (!prefix) return;
      const endpoint = action === "confirm" ? `/commerce/${prefix}/${id}/confirm?company_id=${companyId}`
        : action === "inventory" ? `/commerce/${prefix}/${id}/${isSale ? "post-inventory" : "receive"}?company_id=${companyId}`
        : action === "approve" || action === "reject" ? `/commerce/${prefix}/${id}/approval-decision?company_id=${companyId}`
        : null;
      if (!endpoint) return;
      if (action === "approve" || action === "reject") await client.post(endpoint, { decision: action });
      else await client.post(endpoint);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تنفيذ العملية");
    }
  }

  async function loadDateFormat() {
    if (!companyId) { setDateFormat("DD/MM/YYYY"); return; }
    try {
      const response = await client.get("/company-settings", { params: { company_id: companyId } });
      const value = response.data?.settings?.find((setting: { key?: string }) => setting.key === "general.date_format")?.value;
      const resolved = isCompanyDateFormat(value) ? value : "DD/MM/YYYY";
      setDateFormat(resolved);
      setCompanyDateFormat(companyId, resolved);
    } catch {
      // A policy-settings outage must not block document operations.
      setDateFormat("DD/MM/YYYY");
      setCompanyDateFormat(companyId, "DD/MM/YYYY");
    }
  }

  async function loadPayments() {
    if (!companyId || (!isSale && !isPurchase)) { setPayments([]); return; }
    try {
      const r = await client.get(`/commerce/payments?company_id=${companyId}&document_kind=${isSale ? "sale" : "purchase"}`);
      setPayments(Array.isArray(r.data) ? r.data : []);
    } catch { setPayments([]); }
  }

  async function recordPayment(id: number) {
    if (!companyId || !paymentAmount) return;
    setError("");
    try {
      await client.post(`/commerce/${isSale ? "sales" : "purchases"}/${id}/payments`, {
        company_id: companyId,
        document_id: id,
        payment_date: getLocalISODate(),
        amount: Number(paymentAmount),
        method: paymentMethod,
        ...(paymentMethod === "cheque" ? { cheque_number: chequeNumber, cheque_bank_name: chequeBank || null, cheque_due_date: chequeDueDate } : {}),
      });
      setPaymentAmount("");
      setChequeNumber("");
      setChequeBank("");
      await Promise.all([load(), loadPayments()]);
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر تسجيل الدفعة"); }
  }

  async function reversePayment(paymentId: number) {
    if (!companyId) return;
    setError("");
    try {
      await client.post(`/commerce/payments/${paymentId}/reverse`, {
        company_id: companyId,
        reversal_date: getLocalISODate(),
      });
      await Promise.all([load(), loadPayments()]);
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر عكس الدفعة"); }
  }

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
      const params = new URLSearchParams(query.replace(/^\?/, "")); if (meta.partnerType) params.set("partner_type", meta.partnerType); if (meta.documentType) params.set("document_type", meta.documentType); const r = await client.get(`${meta.endpoint}?${params.toString()}`);
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل البيانات");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); void loadPayments(); void loadDateFormat(); }, [meta.endpoint, query]);

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
        await client.post("/commerce/partners", { company_id: companyId, code, name, partner_type: meta.partnerType || "customer" });
      } else if (meta.kind === "documents") {
        await client.post(meta.endpoint, {
          company_id: companyId,
          partner_id: Number(partnerId),
          document_type: type,
          number,
          document_date: getLocalISODate(),
          ...(sourceOrderId ? { source_order_id: Number(sourceOrderId) } : {}),
          ...(type === "bill" && receiptIds.trim() ? { receipt_ids: receiptIds.split(",").map(value => Number(value.trim())).filter(value => Number.isInteger(value) && value > 0) } : {}),
          lines: [{
            item_id: Number(itemId),
            description: name,
            quantity: 1,
            unit_price: Number(amount || 0),
            ...(sourceLineId && isSale ? { source_sales_line_id: Number(sourceLineId) } : {}),
            ...(sourceLineId && isPurchase ? { source_purchase_line_id: Number(sourceLineId) } : {}),
          }],
        });
      } else {
        await client.post("/shipping/carriers", { company_id: companyId, code, name });
      }
      setName(""); setCode(""); setPartnerId(""); setItemId(""); setNumber(""); setSourceOrderId(""); setSourceLineId(""); setReceiptIds(""); setAmount("");
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
        {meta.kind !== "documents" && <input required value={code} onChange={e => setCode(e.target.value)} placeholder="الكود" className="w-full rounded-lg border bg-background px-3 py-2" />}
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="الاسم / الوصف" className="w-full rounded-lg border bg-background px-3 py-2" />
        {meta.kind === "documents" && <>
          <input required type="number" min="1" value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="Partner ID" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required type="number" min="1" value={itemId} onChange={e => setItemId(e.target.value)} placeholder="Item ID" className="w-full rounded-lg border bg-background px-3 py-2" />
          {isPurchase ? <input required value={number} onChange={e => setNumber(e.target.value)} placeholder="رقم مستند المشتريات" className="w-full rounded-lg border bg-background px-3 py-2" /> : <p className="rounded-lg border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">رقم مستند المبيعات بيتولد تلقائيًا حسب إعدادات الشركة.</p>}
          <select value={type} onChange={e => setType(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2">
            {allowedDocumentTypes.map(value => <option key={value} value={value}>{value}</option>)}
          </select>
          {((isSale && ["delivery", "invoice"].includes(type)) || (isPurchase && ["receipt", "bill"].includes(type))) && <>
            <input type="number" min="1" value={sourceOrderId} onChange={e => setSourceOrderId(e.target.value)} placeholder="رقم أمر المصدر" className="w-full rounded-lg border bg-background px-3 py-2" />
            <input type="number" min="1" value={sourceLineId} onChange={e => setSourceLineId(e.target.value)} placeholder="رقم بند أمر المصدر" className="w-full rounded-lg border bg-background px-3 py-2" />
          </>}
          {isPurchase && type === "bill" && <input value={receiptIds} onChange={e => setReceiptIds(e.target.value)} placeholder="أرقام إذون الاستلام (مفصولة بفاصلة)" className="w-full rounded-lg border bg-background px-3 py-2" />}
          <input required type="number" min="0" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="سعر الوحدة" className="w-full rounded-lg border bg-background px-3 py-2" />
        </>}
        {error && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button disabled={saving || !companyId} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "حفظ"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4"><h2 className="font-semibold">السجلات</h2><button onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-8 text-center text-sm text-muted-foreground">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">لا توجد سجلات.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40">{Object.keys(rows[0]).slice(0, 8).map(k => <th key={k} className="whitespace-nowrap px-4 py-3 text-right font-semibold">{k}</th>)}{(isSale || isPurchase) && <th className="whitespace-nowrap px-4 py-3 text-right font-semibold">إجراءات</th>}</tr></thead><tbody>{rows.map((r, i) => <tr key={String(r.id ?? i)} className="border-b last:border-0">{Object.keys(rows[0]).slice(0, 8).map(k => <td key={k} className="whitespace-nowrap px-4 py-3">{(() => { const value = String(r[k] ?? "—"); return formatCompanyDate(value, dateFormat); })()}</td>)}{(isSale || isPurchase) && <td className="whitespace-nowrap px-4 py-3"><div className="flex gap-2">{r.status === "pending_approval" ? <><button type="button" onClick={() => void actionDocument(Number(r.id), "approve")} className="rounded border px-2 py-1 text-xs">موافقة</button><button type="button" onClick={() => void actionDocument(Number(r.id), "reject")} className="rounded border px-2 py-1 text-xs text-destructive">رفض</button></> : (r.status === "draft" || r.status === "approved") ? <button type="button" onClick={() => void actionDocument(Number(r.id), "confirm")} className="rounded border px-2 py-1 text-xs">تأكيد</button> : null}{(r.document_type === "delivery" || r.document_type === "receipt") && <button type="button" onClick={() => void actionDocument(Number(r.id), "inventory")} className="rounded border px-2 py-1 text-xs">مخزون</button>}<div className="mt-2 flex gap-1"><input type="number" min="0.01" step="0.01" value={paymentAmount} onChange={e => setPaymentAmount(e.target.value)} placeholder="مبلغ" className="w-20 rounded border px-1 py-1 text-xs" /><select value={paymentMethod} onChange={e => setPaymentMethod(e.target.value)} className="rounded border px-1 py-1 text-xs"><option value="bank">Bank</option><option value="cash">Cash</option><option value="cheque">Cheque</option><option value="transfer">Transfer</option></select>{paymentMethod === "cheque" && <><input value={chequeNumber} onChange={e => setChequeNumber(e.target.value)} placeholder="رقم الشيك" className="w-24 rounded border px-1 py-1 text-xs" /><input value={chequeBank} onChange={e => setChequeBank(e.target.value)} placeholder="البنك" className="w-20 rounded border px-1 py-1 text-xs" /><input type="date" value={chequeDueDate} onChange={e => setChequeDueDate(e.target.value)} className="rounded border px-1 py-1 text-xs" /></>}<button type="button" onClick={() => void recordPayment(Number(r.id))} className="rounded border px-2 py-1 text-xs">دفع</button></div>{payments.filter(p => Number(p.document_id) === Number(r.id) && p.status === "posted").map(p => <button key={String(p.id)} type="button" onClick={() => void reversePayment(Number(p.id))} className="mt-1 block rounded border border-destructive/40 px-2 py-1 text-xs text-destructive">عكس دفعة {String(p.amount)}</button>)}</div></td>}</tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
