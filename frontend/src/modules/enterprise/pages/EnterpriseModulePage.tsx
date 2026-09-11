import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
type Field = { key: string; label: string; type?: "text" | "number" | "date"; required?: boolean; min?: number };
type Config = { title: string; description: string; endpoint: string; fields: Field[] };

const configs: Record<string, Config> = {
  assets: { title: "الأصول الثابتة", description: "تسجيل الأصل مع بيانات الاقتناء والعمر والقيمة التخريدية.", endpoint: "/enterprise/assets", fields: [
    { key: "code", label: "كود الأصل", required: true }, { key: "name", label: "اسم الأصل", required: true }, { key: "category", label: "التصنيف", required: true }, { key: "acquisition_date", label: "تاريخ الاقتناء", type: "date", required: true }, { key: "cost", label: "التكلفة", type: "number", required: true, min: 0 }, { key: "residual_value", label: "القيمة التخريدية", type: "number", min: 0 }, { key: "useful_life_months", label: "العمر الإنتاجي بالشهور", type: "number", required: true, min: 1 },
  ] },
  budgets: { title: "الموازنات", description: "إنشاء الموازنة ثم إضافة بنودها واعتمادها من دورة الموازنة.", endpoint: "/enterprise/budgets", fields: [
    { key: "name", label: "اسم الموازنة", required: true }, { key: "fiscal_year", label: "السنة المالية", type: "number", required: true, min: 2001 }, { key: "notes", label: "ملاحظات" },
  ] },
  hr: { title: "الموظفون والرواتب", description: "ملف الموظف الأساسي والراتب قبل تشغيل Payroll.", endpoint: "/enterprise/employees", fields: [
    { key: "employee_no", label: "رقم الموظف", required: true }, { key: "name", label: "اسم الموظف", required: true }, { key: "department", label: "الإدارة" }, { key: "job_title", label: "المسمى الوظيفي" }, { key: "hire_date", label: "تاريخ التعيين", type: "date", required: true }, { key: "basic_salary", label: "الراتب الأساسي", type: "number", required: true, min: 0 }, { key: "allowances", label: "البدلات", type: "number", min: 0 }, { key: "deductions", label: "الاستقطاعات", type: "number", min: 0 },
  ] },
  projects: { title: "المشروعات", description: "تعريف المشروع وربطه بالعميل والتواريخ والميزانية.", endpoint: "/enterprise/projects", fields: [
    { key: "code", label: "كود المشروع", required: true }, { key: "name", label: "اسم المشروع", required: true }, { key: "customer_id", label: "رقم العميل (اختياري)", type: "number", min: 1 }, { key: "start_date", label: "تاريخ البداية", type: "date" }, { key: "end_date", label: "تاريخ النهاية", type: "date" }, { key: "budget", label: "الميزانية", type: "number", min: 0 }, { key: "description", label: "الوصف" },
  ] },
  contracts: { title: "العقود", description: "العقد مرتبط بمشروع وقيمته واستقطاعه، مع التحقق من الشركة في الـ Backend.", endpoint: "/enterprise/contracts", fields: [
    { key: "project_id", label: "رقم المشروع", type: "number", required: true, min: 1 }, { key: "contract_no", label: "رقم العقد", required: true }, { key: "customer_id", label: "رقم العميل (اختياري)", type: "number", min: 1 }, { key: "contract_value", label: "قيمة العقد", type: "number", required: true, min: 0 }, { key: "start_date", label: "تاريخ البداية", type: "date" }, { key: "end_date", label: "تاريخ النهاية", type: "date" }, { key: "retention_percent", label: "نسبة الاستقطاع %", type: "number", min: 0 }, { key: "terms", label: "الشروط" },
  ] },
};

function activeCompanyId(): number | null {
  const value = Number(localStorage.getItem("company_id"));
  return Number.isInteger(value) && value > 0 ? value : null;
}

function errorText(error: unknown): string {
  const detail = (error as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((item) => typeof item === "string" ? item : String((item as { msg?: unknown })?.msg ?? "قيمة غير صحيحة")).join("، ");
  return "تعذر تنفيذ العملية";
}

export default function EnterpriseModulePage({ module }: { module: keyof typeof configs }) {
  const config = configs[module];
  const [rows, setRows] = useState<Row[]>([]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const cid = activeCompanyId();
  const query = useMemo(() => cid ? `?company_id=${cid}` : "", [cid]);

  const load = useCallback(async () => {
    if (!cid) { setRows([]); setError("اختر شركة فعالة أولاً."); setLoading(false); return; }
    setLoading(true); setError("");
    try { const response = await client.get(`${config.endpoint}${query}`); setRows(Array.isArray(response.data) ? response.data : []); }
    catch (e) { setError(errorText(e)); }
    finally { setLoading(false); }
  }, [cid, config.endpoint, query]);

  useEffect(() => { void load(); }, [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!cid) { setError("اختر شركة فعالة أولاً."); return; }
    setSaving(true); setError("");
    try {
      const payload: Record<string, unknown> = { company_id: cid };
      for (const field of config.fields) {
        const raw = (values[field.key] ?? "").trim();
        if (field.required && !raw) { setError(`أدخل ${field.label}.`); return; }
        if (!raw) continue;
        if (field.type === "number") {
          const number = Number(raw);
          if (!Number.isFinite(number) || (field.min !== undefined && number < field.min)) { setError(`تحقق من ${field.label}.`); return; }
          payload[field.key] = number;
        } else payload[field.key] = raw;
      }
      await client.post(config.endpoint, payload);
      setValues({});
      await load();
    } catch (e) { setError(errorText(e)); }
    finally { setSaving(false); }
  }

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 10) : [];
  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">{config.title}</h1><p className="mt-1 text-sm text-muted-foreground">{config.description}</p></header>
    <div className="grid gap-6 xl:grid-cols-[400px_1fr]">
      <form onSubmit={submit} className="space-y-3 rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="font-semibold">إضافة سجل</h2>
        {config.fields.map((field) => <input key={field.key} required={field.required} min={field.min} type={field.type ?? "text"} value={values[field.key] ?? ""} onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))} placeholder={field.label} className="w-full rounded-lg border bg-background px-3 py-2" />)}
        {error && <div role="alert" className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button type="submit" disabled={saving || loading || !cid} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "حفظ"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4"><div><h2 className="font-semibold">السجلات</h2><p className="text-xs text-muted-foreground">{rows.length} سجل</p></div><button type="button" onClick={() => void load()} disabled={loading} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-10 text-center text-sm text-muted-foreground">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-10 text-center text-sm text-muted-foreground">لا توجد سجلات للشركة الحالية.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40">{columns.map((key) => <th key={key} className="whitespace-nowrap px-4 py-3 text-right">{key.replaceAll("_", " ")}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)} className="border-b last:border-0 hover:bg-muted/20">{columns.map((key) => <td key={key} className="whitespace-nowrap px-4 py-3">{String(row[key] ?? "—")}</td>)}</tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
