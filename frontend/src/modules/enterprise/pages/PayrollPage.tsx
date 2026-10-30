import { FormEvent, useCallback, useEffect, useState } from "react";
import client from "@/shared/api/client";

type PayrollRun = {
  id: number; company_id: number; period: string; status: string;
  total_gross: string | number; total_deductions: string | number; total_net: string | number;
};

function activeCompany(): number | null {
  try {
    const id = Number(localStorage.getItem("company_id"));
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch { return null; }
}

const statusLabels: Record<string, string> = {
  draft: "مسودة",
  pending_approval: "بانتظار الاعتماد",
  ready_to_post: "جاهز للترحيل",
  journal_pending: "القيد بانتظار الاعتماد",
  posted: "مُرحّل",
  rejected: "مرفوض",
};

export default function PayrollPage() {
  const companyId = activeCompany();
  const [period, setPeriod] = useState(() => new Date().toISOString().slice(0, 7));
  const [approvers, setApprovers] = useState("");
  const [runs, setRuns] = useState<PayrollRun[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    if (!companyId) {
      setRuns([]);
      setError("اختر شركة فعالة أولاً.");
      return;
    }
    setError("");
    try {
      const response = await client.get("/enterprise/payroll/runs", { params: { company_id: companyId } });
      setRuns(Array.isArray(response.data) ? response.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل مسيرات الرواتب.");
    }
  }, [companyId]);

  useEffect(() => { void load(); }, [load]);

  async function createRun(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await client.post("/enterprise/payroll/runs", { company_id: companyId, period });
      setNotice("تم إنشاء مسيرة الرواتب كمسودة.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر إنشاء مسيرة الرواتب.");
    } finally { setBusy(false); }
  }

  async function submitRun(runId: number) {
    if (!companyId) return;
    const ids = approvers.split(",").map(value => Number(value.trim())).filter(value => Number.isInteger(value) && value > 0);
    setBusy(true); setError(""); setNotice("");
    try {
      await client.post(`/enterprise/payroll/runs/${runId}/submit`, { approver_ids: ids }, { params: { company_id: companyId } });
      setNotice("تم إرسال المسيرة للمرحلة التالية حسب سياسة اعتماد الرواتب.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر إرسال مسيرة الرواتب.");
    } finally { setBusy(false); }
  }

  async function decideRun(runId: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError(""); setNotice("");
    try {
      await client.post(`/enterprise/payroll/runs/${runId}/decision`, { decision }, { params: { company_id: companyId } });
      setNotice(decision === "approve" ? "تم اعتماد المسيرة." : "تم رفض المسيرة.");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تنفيذ قرار الاعتماد.");
    } finally { setBusy(false); }
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">مسيرات الرواتب</h1><p className="mt-1 text-sm text-muted-foreground">إنشاء المسيرات ومتابعة الاعتماد وحالة الترحيل المحاسبي.</p></header>
    {!companyId && <div role="alert" className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-3 text-sm">{error}</div>}
    {error && companyId && <div role="alert" className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
    {notice && <div role="status" className="rounded-xl border p-3 text-sm">{notice}</div>}
    <form onSubmit={createRun} className="flex flex-wrap items-end gap-3 rounded-2xl border bg-card p-5">
      <label className="space-y-1 text-sm"><span>فترة الرواتب</span><input required type="month" value={period} onChange={e => setPeriod(e.target.value)} className="block rounded-lg border bg-background px-3 py-2" /></label>
      <button disabled={busy || !companyId} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">إنشاء مسيرة</button>
    </form>
    <div className="rounded-2xl border bg-card p-5">
      <label className="block max-w-xl space-y-1 text-sm"><span>أرقام المستخدمين المعتمدين (افصل بينها بفاصلة عند اشتراط الاعتماد)</span><input value={approvers} onChange={e => setApprovers(e.target.value)} placeholder="مثال: 12,15" className="w-full rounded-lg border bg-background px-3 py-2" /></label>
      <div className="mt-4 overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b text-right"><th className="p-2">الفترة</th><th className="p-2">إجمالي المستحق</th><th className="p-2">الاستقطاعات</th><th className="p-2">صافي الرواتب</th><th className="p-2">الحالة</th><th className="p-2">الإجراءات</th></tr></thead>
        <tbody>{runs.map(run => <tr key={run.id} className="border-b last:border-0"><td className="p-2">{run.period}</td><td className="p-2">{Number(run.total_gross).toLocaleString()}</td><td className="p-2">{Number(run.total_deductions).toLocaleString()}</td><td className="p-2">{Number(run.total_net).toLocaleString()}</td><td className="p-2">{statusLabels[run.status] || run.status}</td><td className="p-2"><div className="flex flex-wrap gap-2">{run.status === "draft" && <button type="button" disabled={busy} onClick={() => void submitRun(run.id)} className="rounded border px-2 py-1">إرسال للاعتماد</button>}{run.status === "pending_approval" && <><button type="button" disabled={busy} onClick={() => void decideRun(run.id, "approve")} className="rounded border px-2 py-1">اعتماد</button><button type="button" disabled={busy} onClick={() => void decideRun(run.id, "reject")} className="rounded border px-2 py-1 text-destructive">رفض</button></>}</div></td></tr>)}</tbody></table>{runs.length === 0 && <p className="p-6 text-center text-muted-foreground">لا توجد مسيرات رواتب.</p>}</div>
      <p className="mt-3 text-xs text-muted-foreground">الترحيل إلى الأستاذ العام يتطلب تحديد الفرع والدفتر والفترة والحسابات المحاسبية؛ لن يتم ترحيل المسيرة تلقائيًا دون هذه البيانات.</p>
    </div>
  </section>;
}
