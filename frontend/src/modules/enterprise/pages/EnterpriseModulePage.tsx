import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
type Config = {
  title: string;
  description: string;
  endpoint: string;
  createFields: Array<{ key: string; label: string; type?: string; required?: boolean }>;
};

const configs: Record<string, Config> = {
  assets: { title: "الأصول الثابتة", description: "الأصول والتكلفة والإهلاك والقيمة الدفترية.", endpoint: "/enterprise/assets", createFields: [{ key: "code", label: "كود الأصل", required: true }, { key: "name", label: "اسم الأصل", required: true }, { key: "cost", label: "التكلفة", type: "number", required: true }, { key: "residual_value", label: "القيمة التخريدية", type: "number" }, { key: "useful_life_months", label: "العمر الإنتاجي بالشهور", type: "number", required: true }] },
  budgets: { title: "الموازنات", description: "إنشاء الموازنة وإدارتها ثم اعتمادها في دورة مستقلة.", endpoint: "/enterprise/budgets", createFields: [{ key: "code", label: "كود الموازنة", required: true }, { key: "name", label: "اسم الموازنة", required: true }, { key: "fiscal_year", label: "السنة المالية", type: "number", required: true }] },
  hr: { title: "الموظفون والرواتب", description: "ملفات الموظفين وتشغيل الرواتب على مستوى الشركة الحالية.", endpoint: "/enterprise/employees", createFields: [{ key: "employee_no", label: "رقم الموظف", required: true }, { key: "name", label: "اسم الموظف", required: true }, { key: "basic_salary", label: "الراتب الأساسي", type: "number", required: true }, { key: "allowances", label: "البدلات", type: "number" }, { key: "deductions", label: "الاستقطاعات", type: "number" }] },
  projects: { title: "المشروعات", description: "المشروعات والتكلفة والميزانية ومتابعة التنفيذ.", endpoint: "/enterprise/projects", createFields: [{ key: "code", label: "كود المشروع", required: true }, { key: "name", label: "اسم المشروع", required: true }, { key: "budget", label: "الميزانية", type: "number" }] },
  contracts: { title: "العقود", description: "عقود المشروعات وقيمتها وفترتها والاستقطاع.", endpoint: "/enterprise/contracts", createFields: [{ key: "contract_no", label: "رقم العقد", required: true }, { key: "project_id", label: "رقم المشروع", type: "number", required: true }, { key: "value", label: "قيمة العقد", type: "number", required: true }] },
};

function companyId(): number | null {
  const value = Number(localStorage.getItem("company_id"));
  return Number.isInteger(value) && value > 0 ? value : null;
}

function errorText(e: unknown): string {
  const detail = (e as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  return typeof detail === "string" ? detail : "تعذر تنفيذ العملية";
}

export default function EnterpriseModulePage({ module }: { module: keyof typeof configs }) {
  const config = configs[module];
  const [rows, setRows] = useState<Row[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const cid = companyId();

  const query = useMemo(() => cid ? `?company_id=${cid}` : "", [cid]);
  const load = useCallback(async () => {
    if (!cid) { setRows([]); setError("اختر شركة فعالة أولاً."); setLoading(false); return; }
    setLoading(true); setError("");
    try { const response = await client.get(`${config.endpoint}${query}`); setRows(Array.isArray(response.data) ? response.data : []); }
    catch (e) { setError(errorText(e)); }
    finally { setLoading(false); }
  }, [cid, config.endpoint, query]);

  useEffect(() => { void load(); }, [load]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!cid) return setError("اختر شركة فعالة أولاً.");
    setSaving(true); setError("");
    try {
      const payload: Record<string, unknown> = { company_id: cid };
      for (const field of config.createFields) {
        const raw = values[field.key] ?? "";
        if (field.required && !raw.trim()) { setError(`أدخل ${field.label}.`); return; }
        payload[field.key] = field.type === "number" ? Number(raw) : raw.trim();
      }
      await client.post(config.endpoint, payload);
      setValues({});
      await load();
    } catch (e) { setError(errorText(e)); }
    finally { setSaving(false); }
  }

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 8) : [];
  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">{config.title}</h1><p className="mt-1 text-sm text-muted-foreground">{config.description}</p></header>
    <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
      <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="font-semibold">إضافة سجل</h2>
        {config.createFields.map((field) => <input key={field.key} required={field.required} type={field.type ?? "text"} value={values[field.key] ?? ""} onChange={(e) => setValues((current) => ({ ...current, [field.key]: e.target.value }))} placeholder={field.label} className="w-full rounded-lg border bg-background px-3 py-2" />)}
        {error && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button disabled={saving || !cid} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "حفظ"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4"><div><h2 className="font-semibold">السجلات</h2><p className="text-xs text-muted-foreground">{rows.length} سجل</p></div><button type="button" onClick={() => void load()} disabled={loading} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-10 text-center text-sm text-muted-foreground">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-10 text-center text-sm text-muted-foreground">لا توجد سجلات.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40">{columns.map((key) => <th key={key} className="whitespace-nowrap px-4 py-3 text-right">{key.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={String(row.id ?? i)} className="border-b last:border-0 hover:bg-muted/20">{columns.map((key) => <td key={key} className="whitespace-nowrap px-4 py-3">{String(row[key] ?? "—")}</td>)}</tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
