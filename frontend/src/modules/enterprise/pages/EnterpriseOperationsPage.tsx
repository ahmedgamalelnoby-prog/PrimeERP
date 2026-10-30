import { FormEvent, useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Row = Record<string, unknown>;
type Area = "assets" | "budgets" | "projects" | "contracts";

const areas: Record<Area, { title: string; endpoint: string }> = {
  assets: { title: "الأصول الثابتة", endpoint: "/enterprise/assets" },
  budgets: { title: "الموازنات", endpoint: "/enterprise/budgets" },
  projects: { title: "المشروعات", endpoint: "/enterprise/projects" },
  contracts: { title: "العقود", endpoint: "/enterprise/contracts" },
};

const fields: Record<Area, Array<{ key: string; label: string; type?: string; required?: boolean }>> = {
  assets: [
    { key: "code", label: "كود الأصل", required: true },
    { key: "name", label: "اسم الأصل", required: true },
    { key: "category", label: "الفئة", required: true },
    { key: "acquisition_date", label: "تاريخ الاقتناء", type: "date", required: true },
    { key: "cost", label: "التكلفة", type: "number", required: true },
    { key: "residual_value", label: "القيمة التخريدية", type: "number" },
    { key: "useful_life_months", label: "العمر الإنتاجي بالشهور", type: "number", required: true },
  ],
  budgets: [
    { key: "name", label: "اسم الموازنة", required: true },
    { key: "fiscal_year", label: "السنة المالية", type: "number", required: true },
    { key: "notes", label: "ملاحظات" },
  ],
  projects: [
    { key: "code", label: "كود المشروع", required: true },
    { key: "name", label: "اسم المشروع", required: true },
    { key: "customer_id", label: "رقم العميل (اختياري)", type: "number" },
    { key: "start_date", label: "تاريخ البداية", type: "date" },
    { key: "end_date", label: "تاريخ النهاية", type: "date" },
    { key: "budget", label: "الموازنة", type: "number" },
    { key: "description", label: "الوصف" },
  ],
  contracts: [
    { key: "project_id", label: "رقم المشروع", type: "number", required: true },
    { key: "contract_no", label: "رقم العقد", required: true },
    { key: "customer_id", label: "رقم العميل (اختياري)", type: "number" },
    { key: "contract_value", label: "قيمة العقد", type: "number", required: true },
    { key: "start_date", label: "تاريخ البداية", type: "date" },
    { key: "end_date", label: "تاريخ النهاية", type: "date" },
    { key: "retention_percent", label: "نسبة الاستقطاع", type: "number" },
    { key: "terms", label: "الشروط" },
  ],
};

function companyId(): number | null {
  try {
    const value = Number(localStorage.getItem("company_id"));
    return Number.isInteger(value) && value > 0 ? value : null;
  } catch {
    return null;
  }
}

export default function EnterpriseOperationsPage() {
  const path = useLocation().pathname;
  const segments = path.split("/").filter(Boolean);
  const area = (segments[segments.length - 1] || "assets") as Area;
  const config = areas[area] || areas.assets;
  const company = companyId();
  const [rows, setRows] = useState<Row[]>([]);
  const [form, setForm] = useState<Record<string, string>>({});
  const [lineForm, setLineForm] = useState({ budget_id: "", account_id: "", period: "1", amount: "" });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!company) {
      setRows([]);
      setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");
      return;
    }
    setError("");
    try {
      const response = await client.get(config.endpoint, { params: { company_id: company } });
      setRows(Array.isArray(response.data) ? response.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل البيانات");
    }
  }, [company, config.endpoint]);

  useEffect(() => { void load(); }, [load]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!company) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const payload: Record<string, unknown> = { company_id: company, ...form };
      for (const key of ["cost", "residual_value", "useful_life_months", "fiscal_year", "customer_id", "budget", "project_id", "contract_value", "retention_percent"]) {
        if (key in payload && payload[key] !== "") payload[key] = Number(payload[key]);
      }
      for (const key of ["customer_id", "start_date", "end_date", "notes", "description", "terms"]) {
        if (payload[key] === "") payload[key] = null;
      }
      if (area === "assets" && !("residual_value" in payload)) payload.residual_value = 0;
      if (area === "projects" && !("budget" in payload)) payload.budget = 0;
      if (area === "contracts" && !("retention_percent" in payload)) payload.retention_percent = 0;
      await client.post(config.endpoint, payload);
      setForm({});
      setNotice("تم حفظ السجل بنجاح.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر حفظ السجل");
    } finally {
      setBusy(false);
    }
  }

  async function addBudgetLine(e: FormEvent) {
    e.preventDefault();
    if (!company || !lineForm.budget_id) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await client.post(`/enterprise/budgets/${Number(lineForm.budget_id)}/lines`, {
        account_id: Number(lineForm.account_id),
        period: Number(lineForm.period),
        amount: Number(lineForm.amount),
      });
      setNotice("تمت إضافة بند الموازنة.");
      setLineForm({ ...lineForm, account_id: "", amount: "" });
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذرت إضافة بند الموازنة");
    } finally {
      setBusy(false);
    }
  }

  async function approveBudget(id: number) {
    if (!company) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await client.post(`/enterprise/budgets/${id}/approve`, null, { params: { company_id: company } });
      setNotice("تم اعتماد الموازنة.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر اعتماد الموازنة");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">{config.title}</h1>
        <p className="mt-1 text-sm text-muted-foreground">إدارة السجلات حسب الشركة الفعالة، مع التحقق من صلاحيات الخادم.</p>
      </header>
      {!company && <div role="alert" className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm">{error}</div>}
      {error && company && <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
      {notice && <div role="status" className="rounded-xl border p-3 text-sm">{notice}</div>}
      <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
        <form onSubmit={submit} className="space-y-3 rounded-2xl border bg-card p-5">
          <h2 className="font-semibold">إضافة سجل</h2>
          {fields[area] ? fields[area].map(field => (
            <label key={field.key} className="block space-y-1 text-sm">
              <span>{field.label}</span>
              <input
                required={field.required}
                type={field.type || "text"}
                min={field.type === "number" ? 0 : undefined}
                step={field.type === "number" ? "0.01" : undefined}
                value={form[field.key] || ""}
                onChange={event => setForm(current => ({ ...current, [field.key]: event.target.value }))}
                className="w-full rounded-lg border bg-background px-3 py-2"
              />
            </label>
          )) : null}
          <button disabled={busy || !company} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">
            {busy ? "جارٍ الحفظ..." : "حفظ"}
          </button>
        </form>
        <div className="space-y-4">
          {area === "budgets" && (
            <form onSubmit={addBudgetLine} className="grid gap-2 rounded-2xl border bg-card p-4 md:grid-cols-4">
              <input required type="number" min="1" placeholder="رقم الموازنة" value={lineForm.budget_id} onChange={e => setLineForm({ ...lineForm, budget_id: e.target.value })} className="rounded-lg border bg-background px-3 py-2" />
              <input required type="number" min="1" placeholder="رقم الحساب" value={lineForm.account_id} onChange={e => setLineForm({ ...lineForm, account_id: e.target.value })} className="rounded-lg border bg-background px-3 py-2" />
              <input required type="number" min="1" max="12" placeholder="الشهر" value={lineForm.period} onChange={e => setLineForm({ ...lineForm, period: e.target.value })} className="rounded-lg border bg-background px-3 py-2" />
              <input required type="number" min="0" step="0.01" placeholder="المبلغ" value={lineForm.amount} onChange={e => setLineForm({ ...lineForm, amount: e.target.value })} className="rounded-lg border bg-background px-3 py-2" />
              <button disabled={busy || !company} className="rounded-lg border px-3 py-2 text-sm disabled:opacity-50">إضافة بند للموازنة</button>
            </form>
          )}
          <div className="overflow-hidden rounded-2xl border bg-card">
            <div className="flex items-center justify-between border-b p-4">
              <h2 className="font-semibold">السجلات ({rows.length})</h2>
              <button type="button" onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button>
            </div>
            {rows.length === 0 ? <p className="p-8 text-center text-sm text-muted-foreground">لا توجد سجلات.</p> : (
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b bg-muted/40">{Object.keys(rows[0]).map(key => <th key={key} className="whitespace-nowrap px-3 py-2 text-right">{key}</th>)}{area === "budgets" && <th className="px-3 py-2">إجراء</th>}</tr></thead>
                  <tbody>{rows.map((row, index) => <tr key={String(row.id ?? index)} className="border-b last:border-0">
                    {Object.keys(rows[0]).map(key => <td key={key} className="whitespace-nowrap px-3 py-2">{String(row[key] ?? "—")}</td>)}
                    {area === "budgets" && <td className="px-3 py-2">{row.status === "draft" && <button type="button" disabled={busy} onClick={() => void approveBudget(Number(row.id))} className="rounded border px-2 py-1 text-xs disabled:opacity-50">اعتماد</button>}</td>}
                  </tr>)}</tbody>
                </table>
              </div>
            )}
          </div>
          {area === "assets" && <p className="text-xs text-muted-foreground">ترحيل الإهلاك إلى الأستاذ العام غير متاح حاليًا؛ لن يتم تسجيل إهلاك غير مربوط بقيد محاسبي متوازن.</p>}
        </div>
      </div>
    </section>
  );
}
