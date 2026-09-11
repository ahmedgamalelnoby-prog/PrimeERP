import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
type Option = { id: number; label: string };
type ScreenKind = "partners" | "documents" | "shipping";

type ScreenConfig = {
  title: string;
  description: string;
  endpoint: string;
  kind: ScreenKind;
  documentType?: string;
  documentLabel?: string;
  partnerType?: "customer" | "vendor" | "both";
};

const screens: Record<string, ScreenConfig> = {
  "/customers": {
    title: "العملاء والموردون",
    description: "إدارة الأطراف التجارية للشركة الحالية بدون خلط بيانات الشركات أو الـ tenant.",
    endpoint: "/commerce/partners",
    kind: "partners",
    partnerType: "customer",
  },
  "/sales/quotations": {
    title: "عروض المبيعات",
    description: "إنشاء ومراجعة عروض المبيعات قبل تحويلها إلى طلب بيع.",
    endpoint: "/commerce/sales/documents",
    kind: "documents",
    documentType: "quotation",
    documentLabel: "عرض مبيعات",
    partnerType: "customer",
  },
  "/sales/orders": {
    title: "طلبات المبيعات",
    description: "طلبات البيع المرتبطة بالعميل والصنف، ثم تأكيدها وترحيل المخزون من دورة المستند.",
    endpoint: "/commerce/sales/documents",
    kind: "documents",
    documentType: "order",
    documentLabel: "طلب مبيعات",
    partnerType: "customer",
  },
  "/purchases/orders": {
    title: "طلبات المشتريات",
    description: "طلبات الشراء المرتبطة بالمورد والأصناف مع الحفاظ على دورة المشتريات المنفصلة.",
    endpoint: "/commerce/purchases/documents",
    kind: "documents",
    documentType: "order",
    documentLabel: "طلب شراء",
    partnerType: "vendor",
  },
  "/shipping": {
    title: "الشحن واللوجستيات",
    description: "إدارة شركات الشحن في الشركة الحالية، مع فصلها عن دورة المبيعات والمشتريات.",
    endpoint: "/shipping/carriers",
    kind: "shipping",
  },
};

function selectedCompanyId(): number | null {
  const raw = localStorage.getItem("company_id");
  const value = raw ? Number(raw) : NaN;
  return Number.isInteger(value) && value > 0 ? value : null;
}

function messageFromError(error: unknown, fallback: string): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((x) => typeof x === "string" ? x : x?.msg ?? "Invalid value").join("، ");
  return fallback;
}

function labelOf(row: Row, fields: string[]): string {
  for (const field of fields) {
    const value = row[field];
    if (value !== null && value !== undefined && String(value).trim()) return String(value);
  }
  return `#${String(row.id ?? "")}`;
}

function visibleColumns(rows: Row[]): string[] {
  if (!rows.length) return [];
  const preferred = ["code", "name", "number", "document_type", "status", "document_date", "subtotal", "tax_total", "total", "paid_total", "is_active"];
  const keys = Object.keys(rows[0]);
  return [...preferred.filter((key) => keys.includes(key)), ...keys.filter((key) => !preferred.includes(key))].slice(0, 8);
}

export default function OperationalPage() {
  const path = useLocation().pathname;
  const meta = screens[path] ?? screens["/customers"];
  const companyId = selectedCompanyId();
  const [rows, setRows] = useState<Row[]>([]);
  const [partners, setPartners] = useState<Option[]>([]);
  const [items, setItems] = useState<Option[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [partnerId, setPartnerId] = useState("");
  const [itemId, setItemId] = useState("");
  const [number, setNumber] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [amount, setAmount] = useState("");
  const [partnerType, setPartnerType] = useState<"customer" | "vendor" | "both">(meta.partnerType ?? "customer");

  const query = useMemo(() => companyId ? `?company_id=${companyId}` : "", [companyId]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    if (!companyId) {
      setRows([]);
      setPartners([]);
      setItems([]);
      setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية تلقائياً.");
      setLoading(false);
      return;
    }

    try {
      const requests: Promise<{ data: unknown }>[] = [client.get(`${meta.endpoint}${query}`)];
      if (meta.kind === "documents") {
        requests.push(client.get(`/commerce/partners${query}&partner_type=${meta.partnerType}`));
        requests.push(client.get(`/inventory/items${query}`));
      }
      const results = await Promise.all(requests);
      const first = results[0].data;
      setRows(Array.isArray(first) ? first as Row[] : []);
      if (meta.kind === "documents") {
        const partnerData = Array.isArray(results[1].data) ? results[1].data as Row[] : [];
        const itemData = Array.isArray(results[2].data) ? results[2].data as Row[] : [];
        setPartners(partnerData.map((row) => ({ id: Number(row.id), label: `${labelOf(row, ["name", "code"])}${row.code ? ` (${row.code})` : ""}` })));
        setItems(itemData.map((row) => ({ id: Number(row.id), label: `${labelOf(row, ["name", "code", "sku"])}${row.code || row.sku ? ` (${String(row.code ?? row.sku)})` : ""}` })));
      }
    } catch (e) {
      setError(messageFromError(e, "تعذر تحميل البيانات"));
    } finally {
      setLoading(false);
    }
  }, [companyId, meta.endpoint, meta.kind, meta.partnerType, query]);

  useEffect(() => { void load(); }, [load]);

  function resetForm() {
    setName(""); setCode(""); setPartnerId(""); setItemId(""); setNumber(""); setQuantity("1"); setAmount("");
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return setError("لا يمكن الحفظ بدون شركة فعالة.");
    setSaving(true);
    setError("");
    try {
      if (meta.kind === "partners") {
        await client.post(meta.endpoint, { company_id: companyId, code: code.trim(), name: name.trim(), partner_type: partnerType });
      } else if (meta.kind === "documents") {
        if (!partnerId || !itemId || !number.trim() || !amount || Number(amount) < 0 || !quantity || Number(quantity) <= 0) {
          setError("أكمل العميل/المورد والصنف والرقم والكمية والسعر بشكل صحيح.");
          return;
        }
        await client.post(meta.endpoint, {
          company_id: companyId,
          partner_id: Number(partnerId),
          document_type: meta.documentType,
          number: number.trim(),
          document_date: new Date().toISOString().slice(0, 10),
          lines: [{ item_id: Number(itemId), description: name.trim() || undefined, quantity: Number(quantity), unit_price: Number(amount) }],
        });
      } else {
        await client.post(meta.endpoint, { company_id: companyId, code: code.trim(), name: name.trim() });
      }
      resetForm();
      await load();
    } catch (e) {
      setError(messageFromError(e, "تعذر حفظ السجل"));
    } finally {
      setSaving(false);
    }
  }

  const columns = visibleColumns(rows);
  const isDocument = meta.kind === "documents";

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header className="space-y-1">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-bold">{meta.title}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{meta.description}</p>
          </div>
          {isDocument && <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">{meta.documentLabel}</span>}
        </div>
      </header>

      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
          <div>
            <h2 className="font-semibold">إنشاء {meta.documentLabel ?? (meta.kind === "shipping" ? "شركة شحن" : "طرف تجاري")}</h2>
            <p className="mt-1 text-xs text-muted-foreground">كل عملية مرتبطة بالشركة الفعالة فقط.</p>
          </div>

          {!isDocument && <>
            <input required value={code} onChange={(e) => setCode(e.target.value)} placeholder="الكود" className="w-full rounded-lg border bg-background px-3 py-2" />
            <input required value={name} onChange={(e) => setName(e.target.value)} placeholder={meta.kind === "shipping" ? "اسم شركة الشحن" : "اسم العميل"} className="w-full rounded-lg border bg-background px-3 py-2" />
            {meta.kind === "partners" && <select value={partnerType} onChange={(e) => setPartnerType(e.target.value as typeof partnerType)} className="w-full rounded-lg border bg-background px-3 py-2">
              <option value="customer">عميل</option><option value="vendor">مورد</option><option value="both">عميل ومورد</option>
            </select>}
          </>}

          {isDocument && <>
            <select required value={partnerId} onChange={(e) => setPartnerId(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2">
              <option value="">اختر {meta.partnerType === "vendor" ? "المورد" : "العميل"}</option>
              {partners.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
            <select required value={itemId} onChange={(e) => setItemId(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2">
              <option value="">اختر الصنف</option>
              {items.map((option) => <option key={option.id} value={option.id}>{option.label}</option>)}
            </select>
            <input required value={number} onChange={(e) => setNumber(e.target.value)} placeholder="رقم المستند" className="w-full rounded-lg border bg-background px-3 py-2" />
            <div className="grid grid-cols-2 gap-3">
              <input required type="number" min="0.0001" step="0.0001" value={quantity} onChange={(e) => setQuantity(e.target.value)} placeholder="الكمية" className="w-full rounded-lg border bg-background px-3 py-2" />
              <input required type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="سعر الوحدة" className="w-full rounded-lg border bg-background px-3 py-2" />
            </div>
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="وصف اختياري" className="w-full rounded-lg border bg-background px-3 py-2" />
          </>}

          {error && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
          <button type="submit" disabled={saving || loading || !companyId} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">
            {saving ? "جارٍ الحفظ..." : "حفظ"}
          </button>
        </form>

        <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b p-4">
            <div><h2 className="font-semibold">السجلات</h2><p className="text-xs text-muted-foreground">{rows.length} سجل</p></div>
            <button type="button" onClick={() => void load()} disabled={loading} className="rounded-lg border px-3 py-1.5 text-sm disabled:opacity-50">تحديث</button>
          </div>
          {loading ? <div className="p-10 text-center text-sm text-muted-foreground">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-10 text-center text-sm text-muted-foreground">لا توجد سجلات للشركة الحالية.</div> : (
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b bg-muted/40">{columns.map((key) => <th key={key} className="whitespace-nowrap px-4 py-3 text-right font-semibold">{key.replaceAll("_", " ")}</th>)}</tr></thead>
                <tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)} className="border-b last:border-0 hover:bg-muted/20">{columns.map((key) => <td key={key} className="whitespace-nowrap px-4 py-3">{String(row[key] ?? "—")}</td>)}</tr>)}</tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
