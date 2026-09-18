import { useEffect, useMemo, useState } from "react";
import PageHeader from "@/components/layout/PageHeader";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

type JournalEntry = {
  id: number; company_id: number; journal_id: number; entry_number: string; entry_date: string;
  posting_date: string | null; description: string; total_debit: string; total_credit: string; status: string;
  branch_id: number; fiscal_year_id: number; period_id: number;
};

const statusLabels: Record<string, string> = {
  draft: "مسودة", pending: "بانتظار الاعتماد", approved: "معتمد", posted: "مرحّل", cancelled: "ملغي", reversed: "معكوس",
};

export default function JournalEntriesPage() {
  const [companyId, setCompanyId] = useState(() => Number(localStorage.getItem("company_id")) || 0);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [details, setDetails] = useState<JournalEntry | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ branchId: "", journalId: "", fiscalYearId: "", periodId: "", entryNumber: "", entryDate: new Date().toISOString().slice(0, 10), description: "", debitAccountId: "", creditAccountId: "", amount: "" });
  const [createBusy, setCreateBusy] = useState(false);

  const loadEntries = async () => {
    if (!companyId) { setEntries([]); setError("اختر شركة فعالة أولاً."); return; }
    setLoading(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/accounting/journal-entries?company_id=${companyId}`);
      if (!response.ok) throw new Error((await response.text()) || "تعذر تحميل القيود اليومية");
      setEntries(await response.json() as JournalEntry[]);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر تحميل البيانات");
    } finally { setLoading(false); }
  };

  useEffect(() => { void loadEntries(); }, [companyId]);

  const createDraft = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!companyId) { setError("اختر شركة فعالة أولاً."); return; }
    const amount = Number(createForm.amount);
    if (!amount || amount <= 0) { setError("أدخل مبلغًا صحيحًا أكبر من صفر."); return; }
    const required = ["branchId", "journalId", "fiscalYearId", "periodId", "entryNumber", "entryDate", "description", "debitAccountId", "creditAccountId"] as const;
    if (required.some(key => !createForm[key].trim())) { setError("أكمل جميع بيانات القيد."); return; }
    setCreateBusy(true); setError(null);
    try {
      const response = await fetch(`${API_BASE}/accounting/journal-entries`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_id: companyId, branch_id: Number(createForm.branchId), journal_id: Number(createForm.journalId),
          fiscal_year_id: Number(createForm.fiscalYearId), period_id: Number(createForm.periodId),
          entry_number: createForm.entryNumber.trim(), entry_date: createForm.entryDate, description: createForm.description.trim(),
          lines: [
            { account_combination_id: Number(createForm.debitAccountId), debit: amount, credit: 0 },
            { account_combination_id: Number(createForm.creditAccountId), debit: 0, credit: amount },
          ],
          currency_code: "EGP", exchange_rate: 1,
        }),
      });
      if (!response.ok) throw new Error((await response.text()) || "تعذر إنشاء مسودة القيد");
      setShowCreate(false);
      setCreateForm(current => ({ ...current, entryNumber: "", description: "", amount: "" }));
      await loadEntries();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر إنشاء القيد");
    } finally { setCreateBusy(false); }
  };

  const action = async (id: number, name: "submit" | "approve" | "post" | "cancel" | "reverse") => {
    setBusy(id); setError(null);
    try {
      const response = await fetch(`${API_BASE}/accounting/journal-entries/${id}/${name}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: name === "reverse" ? JSON.stringify({}) : undefined,
      });
      if (!response.ok) throw new Error((await response.text()) || "تعذر تنفيذ العملية");
      await loadEntries();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر تنفيذ العملية");
    } finally { setBusy(null); }
  };

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    return q ? entries.filter((x) => `${x.entry_number} ${x.description} ${x.status}`.toLowerCase().includes(q)) : entries;
  }, [entries, filter]);

  const totals = useMemo(() => ({
    count: filtered.length,
    debit: filtered.reduce((sum, entry) => sum + Number(entry.total_debit), 0),
    credit: filtered.reduce((sum, entry) => sum + Number(entry.total_credit), 0),
  }), [filtered]);

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="القيود اليومية" description="متابعة دورة المسودة والاعتماد والترحيل والعكس من محرك المحاسبة." />
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">عدد القيود</p><p className="mt-1 text-2xl font-bold">{totals.count}</p></div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">إجمالي المدين</p><p className="mt-1 text-2xl font-bold">{totals.debit.toLocaleString("ar-EG")}</p></div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">إجمالي الدائن</p><p className="mt-1 text-2xl font-bold">{totals.credit.toLocaleString("ar-EG")}</p></div>
      </section>
      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm font-medium">الشركة<input type="number" min={1} value={companyId} onChange={(e) => setCompanyId(Number(e.target.value) || 0)} className="w-28 rounded-lg border bg-background px-3 py-2" /></label>
          <button className="rounded-lg bg-primary px-3 py-2 text-primary-foreground" onClick={() => setShowCreate(true)}>+ إنشاء مسودة</button>
          <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="بحث..." className="w-full max-w-xs rounded-lg border bg-background px-3 py-2" />
          <span className="text-sm text-muted-foreground">{loading ? "جاري التحميل..." : `${filtered.length} قيد`}</span>
        </div>
        {error && <div className="mb-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1100px] text-sm">
            <thead><tr className="border-b text-right text-muted-foreground"><th className="p-3">رقم القيد</th><th className="p-3">التاريخ</th><th className="p-3">الوصف</th><th className="p-3">مدين</th><th className="p-3">دائن</th><th className="p-3">الحالة</th><th className="p-3">إجراءات</th></tr></thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">{entry.entry_number}</td><td className="p-3">{entry.entry_date}</td><td className="p-3">{entry.description}</td>
                  <td className="p-3">{Number(entry.total_debit).toLocaleString("ar-EG")}</td><td className="p-3">{Number(entry.total_credit).toLocaleString("ar-EG")}</td><td className="p-3">{statusLabels[entry.status] ?? entry.status}</td>
                  <td className="flex flex-wrap gap-2 p-3">
                    <button className="rounded-lg border px-2 py-1" onClick={async () => { const r = await fetch(`${API_BASE}/accounting/journal-entries/${entry.id}`); if (r.ok) setDetails(await r.json()); }}>عرض</button>
                    {entry.status === "draft" && <button className="rounded-lg border px-2 py-1" disabled={busy === entry.id} onClick={() => void action(entry.id, "submit")}>إرسال</button>}
                    {entry.status === "pending" && <button className="rounded-lg border px-2 py-1" disabled={busy === entry.id} onClick={() => void action(entry.id, "approve")}>اعتماد</button>}
                    {entry.status === "approved" && <button className="rounded-lg border px-2 py-1" disabled={busy === entry.id} onClick={() => void action(entry.id, "post")}>ترحيل</button>}
                    {entry.status === "pending" && <button className="rounded-lg border px-2 py-1" disabled={busy === entry.id} onClick={() => void action(entry.id, "cancel")}>إلغاء</button>}
                    {entry.status === "posted" && <button className="rounded-lg border px-2 py-1" disabled={busy === entry.id} onClick={() => void action(entry.id, "reverse")}>عكس</button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && !filtered.length && <div className="p-8 text-center text-muted-foreground">لا توجد قيود.</div>}
        </div>
      </section>
      {showCreate && (
        <section className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">إنشاء قيد يومية — مسودة</h2><button className="rounded-lg border px-3 py-1" onClick={() => setShowCreate(false)}>إغلاق</button></div>
          <form onSubmit={createDraft} className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {([["branchId","رقم الفرع"],["journalId","رقم اليومية"],["fiscalYearId","رقم السنة المالية"],["periodId","رقم الفترة"],["debitAccountId","حساب المدين"],["creditAccountId","حساب الدائن"]] as const).map(([key,label]) =>
              <label key={key} className="text-sm font-medium">{label}<input type="number" min={1} required value={createForm[key]} onChange={e => setCreateForm(v => ({...v,[key]:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            )}
            <label className="text-sm font-medium">رقم القيد<input required value={createForm.entryNumber} onChange={e => setCreateForm(v => ({...v,entryNumber:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">التاريخ<input type="date" required value={createForm.entryDate} onChange={e => setCreateForm(v => ({...v,entryDate:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">المبلغ<input type="number" min="0.01" step="0.01" required value={createForm.amount} onChange={e => setCreateForm(v => ({...v,amount:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium sm:col-span-2 lg:col-span-3">الوصف<input required value={createForm.description} onChange={e => setCreateForm(v => ({...v,description:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <div className="flex gap-2 sm:col-span-2 lg:col-span-3"><button type="submit" disabled={createBusy} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{createBusy ? "جاري الإنشاء..." : "إنشاء المسودة"}</button><button type="button" className="rounded-lg border px-4 py-2" onClick={() => setShowCreate(false)}>إلغاء</button></div>
          </form>
          <p className="mt-3 text-xs text-muted-foreground">يتم إنشاء قيد متوازن من سطر مدين وسطر دائن. يجب أن تنتمي الفرع واليومية والسنة والفترة والحسابات إلى الشركة النشطة.</p>
        </section>
      )}
      {details && (
        <section className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">تفاصيل القيد {details.entry_number}</h2><button className="rounded-lg border px-3 py-1" onClick={() => setDetails(null)}>إغلاق</button></div>
          <div className="grid gap-3 text-sm sm:grid-cols-2"><div>التاريخ: {details.entry_date}</div><div>الحالة: {statusLabels[details.status] ?? details.status}</div><div>الفرع: {details.branch_id}</div><div>الفترة: {details.period_id}</div></div>
        </section>
      )}
    </div>
  );
}
