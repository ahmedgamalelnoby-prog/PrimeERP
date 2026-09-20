import { FormEvent, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";

type Row = Record<string, any>;
const companyId = () => {
  const n = Number(localStorage.getItem("company_id"));
  return Number.isInteger(n) && n > 0 ? n : null;
};

const modes = {
  assets: { title: "الأصول الثابتة", endpoint: "/enterprise/assets" },
  budgets: { title: "الموازنات", endpoint: "/enterprise/budgets" },
  hr: { title: "الموظفون والرواتب", endpoint: "/enterprise/employees" },
  projects: { title: "المشروعات", endpoint: "/enterprise/projects" },
  contracts: { title: "العقود", endpoint: "/enterprise/contracts" },
} as const;

type Mode = keyof typeof modes;

function modeFromPath(path: string): Mode {
  if (path.endsWith("/budgets")) return "budgets";
  if (path.endsWith("/hr")) return "hr";
  if (path.endsWith("/projects")) return "projects";
  if (path.endsWith("/contracts")) return "contracts";
  return "assets";
}

export default function EnterprisePage() {
  const mode = modeFromPath(useLocation().pathname);
  const meta = modes[mode];
  const cid = companyId();
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<Record<string, string>>({});
  const [payrollPeriod, setPayrollPeriod] = useState(new Date().toISOString().slice(0, 7));

  const set = (key: string, value: string) => setForm(prev => ({ ...prev, [key]: value }));
  const reset = () => setForm({});

  async function load() {
    if (!cid) { setRows([]); setError("اختر شركة فعالة أولاً."); return; }
    setError("");
    try {
      const r = await client.get(meta.endpoint, { params: { company_id: cid } });
      setRows(Array.isArray(r.data) ? r.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل البيانات");
    }
  }

  useEffect(() => { reset(); void load(); }, [mode, cid]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!cid) return setError("لا يمكن الحفظ بدون شركة فعالة.");
    setSaving(true); setError("");
    try {
      if (mode === "assets") {
        await client.post("/enterprise/assets", {
          company_id: cid, code: form.code, name: form.name, category: form.category,
          acquisition_date: form.acquisition_date, cost: Number(form.cost), residual_value: Number(form.residual_value || 0),
          useful_life_months: Number(form.useful_life_months),
        });
      } else if (mode === "budgets") {
        await client.post("/enterprise/budgets", {
          company_id: cid, name: form.name, fiscal_year: Number(form.fiscal_year), notes: form.notes || null,
        });
      } else if (mode === "hr") {
        await client.post("/enterprise/employees", {
          company_id: cid, employee_no: form.employee_no, name: form.name, department: form.department || null,
          job_title: form.job_title || null, hire_date: form.hire_date, basic_salary: Number(form.basic_salary || 0),
          allowances: Number(form.allowances || 0), deductions: Number(form.deductions || 0),
        });
      } else if (mode === "projects") {
        await client.post("/enterprise/projects", {
          company_id: cid, code: form.code, name: form.name, customer_id: form.customer_id ? Number(form.customer_id) : null,
          start_date: form.start_date || null, end_date: form.end_date || null, budget: Number(form.budget || 0), description: form.description || null,
        });
      } else {
        await client.post("/enterprise/contracts", {
          company_id: cid, project_id: Number(form.project_id), contract_no: form.contract_no,
          customer_id: form.customer_id ? Number(form.customer_id) : null, contract_value: Number(form.contract_value || 0),
          start_date: form.start_date || null, end_date: form.end_date || null,
          retention_percent: Number(form.retention_percent || 0), terms: form.terms || null,
        });
      }
      reset(); await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر حفظ السجل");
    } finally { setSaving(false); }
  }

  async function action(path: string, body?: any) {
    if (!cid) return;
    setError("");
    try { await client.post(path, body); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "تعذر تنفيذ العملية"); }
  }

  const fields = useMemo(() => {
    if (mode === "assets") return [
      ["code","الكود", "text"], ["name","اسم الأصل","text"], ["category","التصنيف","text"],
      ["acquisition_date","تاريخ الاقتناء","date"], ["cost","التكلفة","number"], ["residual_value","القيمة المتبقية","number"], ["useful_life_months","العمر بالأشهر","number"],
    ];
    if (mode === "budgets") return [["name","اسم الموازنة","text"],["fiscal_year","السنة المالية","number"],["notes","ملاحظات","text"]];
    if (mode === "hr") return [
      ["employee_no","رقم الموظف","text"],["name","اسم الموظف","text"],["department","القسم","text"],["job_title","الوظيفة","text"],
      ["hire_date","تاريخ التعيين","date"],["basic_salary","الراتب الأساسي","number"],["allowances","البدلات","number"],["deductions","الاستقطاعات","number"],
    ];
    if (mode === "projects") return [
      ["code","كود المشروع","text"],["name","اسم المشروع","text"],["customer_id","Customer ID","number"],["start_date","البداية","date"],
      ["end_date","النهاية","date"],["budget","الموازنة","number"],["description","الوصف","text"],
    ];
    return [
      ["project_id","Project ID","number"],["contract_no","رقم العقد","text"],["customer_id","Customer ID","number"],
      ["contract_value","قيمة العقد","number"],["start_date","البداية","date"],["end_date","النهاية","date"],
      ["retention_percent","Retention %","number"],["terms","الشروط","text"],
    ];
  }, [mode]);

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">{meta.title}</h1>
      <p className="mt-1 text-sm text-muted-foreground">واجهة تشغيل فعلية مرتبطة بالـ API مع عزل الشركة والـ tenant.</p>
    </header>

    {error && <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}

    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <div className="space-y-4">
        <form onSubmit={submit} className="space-y-3 rounded-2xl border bg-card p-5 shadow-sm">
          <h2 className="font-semibold">إضافة {meta.title}</h2>
          {fields.map(([key, label, type]) =>
            <input key={key} required={!["customer_id","description","notes","terms","residual_value","allowances","deductions","retention_percent"].includes(key)}
              type={type} value={form[key] || ""} onChange={e => set(key, e.target.value)} placeholder={label}
              className="w-full rounded-lg border bg-background px-3 py-2" />
          )}
          <button disabled={saving || !cid} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">
            {saving ? "جارٍ الحفظ..." : "حفظ"}
          </button>
        </form>

        {mode === "assets" && rows.length > 0 && (
          <div className="rounded-2xl border bg-card p-5 shadow-sm">
            <h2 className="font-semibold">إهلاك أصل</h2>
            <p className="mt-1 text-xs text-muted-foreground">التشغيل يتم على الأصل المحدد من القائمة.</p>
            <select id="asset-action" className="mt-3 w-full rounded-lg border px-3 py-2">
              {rows.map(r => <option key={r.id} value={r.id}>{r.code} — {r.name}</option>)}
            </select>
            <button className="mt-3 w-full rounded-lg border px-4 py-2" onClick={() => {
              const id = Number((document.getElementById("asset-action") as HTMLSelectElement).value);
              void action("/enterprise/assets/" + id + "/depreciate?company_id=" + cid + "&months=1");
            }}>ترحيل شهر إهلاك</button>
          </div>
        )}

        {mode === "hr" && (
          <div className="rounded-2xl border bg-card p-5 shadow-sm">
            <h2 className="font-semibold">تشغيل Payroll</h2>
            <input type="month" value={payrollPeriod} onChange={e => setPayrollPeriod(e.target.value)} className="mt-3 w-full rounded-lg border px-3 py-2" />
            <button className="mt-3 w-full rounded-lg border px-4 py-2" onClick={() => void action("/enterprise/payroll/runs", { company_id: cid, period: payrollPeriod })}>إنشاء وترحيل Payroll</button>
          </div>
        )}

        {mode === "budgets" && rows.length > 0 && (
          <div className="rounded-2xl border bg-card p-5 shadow-sm">
            <h2 className="font-semibold">اعتماد الموازنة</h2>
            <select id="budget-action" className="mt-3 w-full rounded-lg border px-3 py-2">
              {rows.map(r => <option key={r.id} value={r.id}>{r.name} — {r.status}</option>)}
            </select>
            <p className="mt-2 text-xs text-muted-foreground">يجب إضافة سطر موازنة واحد على الأقل قبل الاعتماد.</p>
            <button className="mt-3 w-full rounded-lg border px-4 py-2" onClick={() => {
              const id = Number((document.getElementById("budget-action") as HTMLSelectElement).value);
              void action("/enterprise/budgets/" + id + "/approve?company_id=" + cid);
            }}>اعتماد</button>
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="font-semibold">السجلات</h2>
          <button onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button>
        </div>
        {rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">لا توجد سجلات.</div> :
          <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40">
            {Object.keys(rows[0]).slice(0, 10).map(k => <th key={k} className="whitespace-nowrap px-4 py-3 text-right">{k}</th>)}
          </tr></thead><tbody>{rows.map((r, i) => <tr key={String(r.id ?? i)} className="border-b last:border-0">
            {Object.keys(rows[0]).slice(0, 10).map(k => <td key={k} className="whitespace-nowrap px-4 py-3">{String(r[k] ?? "—")}</td>)}
          </tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
