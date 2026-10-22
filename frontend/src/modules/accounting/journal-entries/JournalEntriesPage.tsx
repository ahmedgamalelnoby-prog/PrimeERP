import { useEffect, useMemo, useState, type FormEvent } from "react";
import client from "@/shared/api/client";
import PageHeader from "@/components/layout/PageHeader";
import { formatCompanyDate, useCompanyClockDate, useCompanyDateFormat } from "@/utils/format-date";



type JournalLine = {
  id: number; line_number: number; account_combination_id: number; department_id: number | null; cost_center_id: number | null;
  description: string | null; reference: string | null; debit: string; credit: string; base_debit: string; base_credit: string;
};

type JournalEntry = {
  id: number; company_id: number; journal_id: number; entry_number: string; entry_date: string;
  posting_date: string | null; description: string; total_debit: string; total_credit: string; status: string;
  branch_id: number; fiscal_year_id: number; period_id: number; reference?: string | null; currency_code?: string;
  lines?: JournalLine[];
};

type JournalOption = { id: number; code: string; name_ar: string; name_en: string; journal_type: string; allow_manual_entries: boolean; is_active: boolean };
type AccountOption = { id: number; code: string; name_ar: string; name_en?: string | null; is_active: boolean };

function getStoredCompanyId(): number {
  try {
    const value = Number(localStorage.getItem("company_id"));
    return Number.isInteger(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

const statusLabels: Record<string, string> = {
  draft: "مسودة", pending: "بانتظار الاعتماد", approved: "معتمد", posted: "مرحّل", cancelled: "ملغي", reversed: "معكوس",
};

export default function JournalEntriesPage() {
  const [companyId, setCompanyId] = useState(getStoredCompanyId);
  const dateFormat = useCompanyDateFormat(companyId);
  const { companyDate, error: clockError } = useCompanyClockDate(companyId);
  useEffect(() => { if (clockError) setError(clockError); }, [clockError]);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [journals, setJournals] = useState<JournalOption[]>([]);
  const [accounts, setAccounts] = useState<AccountOption[]>([]);
  const [optionsLoading, setOptionsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<number | null>(null);
  const [filter, setFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [journalFilter, setJournalFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [details, setDetails] = useState<JournalEntry | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ branchId: "", journalId: "", fiscalYearId: "", periodId: "", entryNumber: "", entryDate: "", description: "", debitAccountId: "", creditAccountId: "", amount: "" });
  const [createBusy, setCreateBusy] = useState(false);

  const loadEntries = async () => {
    if (!companyId) { setEntries([]); setError("اختر شركة فعالة أولاً."); return; }
    setLoading(true); setError(null);
    try {
      const params = new URLSearchParams({ company_id: String(companyId) });
      if (statusFilter) params.set("status", statusFilter);
      if (journalFilter) params.set("journal_id", journalFilter);
      if (fromDate) params.set("from_date", fromDate);
      if (toDate) params.set("to_date", toDate);
      const response = await client.get<JournalEntry[]>("/accounting/journal-entries",{params:Object.fromEntries(params)});
      setEntries(response.data);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر تحميل البيانات");
    } finally { setLoading(false); }
  };

  useEffect(() => {
    if (companyDate) setCreateForm(current => current.entryDate ? current : { ...current, entryDate: companyDate });
  }, [companyDate]);

  useEffect(() => {
    void loadEntries();
    if (!companyId) { setJournals([]); setAccounts([]); return; }
    setOptionsLoading(true);
    Promise.all([
      client.get<JournalOption[]>("/accounting/journal-entries/journals",{params:{company_id:companyId}}),
      client.get<AccountOption[]>("/chart-of-accounts/combinations",{params:{company_id:companyId}}),
    ])
      .then(([journalResponse, accountResponse]) => {
        setJournals(journalResponse.data);
        setAccounts(accountResponse.data);
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "تعذر تحميل بيانات المحاسبة"))
      .finally(() => setOptionsLoading(false));
  }, [companyId]);

  const createDraft = async (event: FormEvent) => {
    event.preventDefault();
    if (!companyId) { setError("اختر شركة فعالة أولاً."); return; }
    const amount = Number(createForm.amount);
    if (!amount || amount <= 0) { setError("أدخل مبلغًا صحيحًا أكبر من صفر."); return; }
    if (createForm.debitAccountId === createForm.creditAccountId) { setError("لا يمكن أن يكون حساب المدين هو نفسه حساب الدائن."); return; }
    const required = ["branchId", "journalId", "fiscalYearId", "periodId", "entryNumber", "entryDate", "description", "debitAccountId", "creditAccountId"] as const;
    if (required.some(key => !createForm[key].trim())) { setError("أكمل جميع بيانات القيد."); return; }
    setCreateBusy(true); setError(null);
    try {
      await client.post("/accounting/journal-entries",{
          company_id: companyId, branch_id: Number(createForm.branchId), journal_id: Number(createForm.journalId),
          fiscal_year_id: Number(createForm.fiscalYearId), period_id: Number(createForm.periodId),
          entry_number: createForm.entryNumber.trim(), entry_date: createForm.entryDate, description: createForm.description.trim(),
          lines: [
            { account_combination_id: Number(createForm.debitAccountId), debit: amount, credit: 0 },
            { account_combination_id: Number(createForm.creditAccountId), debit: 0, credit: amount },
          ],
          currency_code: "EGP", exchange_rate: 1,
        });
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
      await client.post(`/accounting/journal-entries/${id}/${name}`, name === "reverse" ? {} : undefined);
      await loadEntries();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر تنفيذ العملية");
    } finally { setBusy(null); }
  };

  const openDetails = async (id: number) => {
    setDetailsLoading(true); setError(null);
    try {
      const response = await client.get<JournalEntry>(`/accounting/journal-entries/${id}`);
      setDetails(response.data);
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "تعذر تحميل تفاصيل القيد");
    } finally { setDetailsLoading(false); }
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

  const accountName = (id: number) => {
    const account = accounts.find(x => x.id === id);
    return account ? `${account.code} — ${account.name_ar}` : `حساب #${id}`;
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader title="القيود اليومية" description="دورة كاملة من المسودة إلى الاعتماد والترحيل والعكس مع البحث والتصفية والتفاصيل." />
      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">عدد القيود</p><p className="mt-1 text-2xl font-bold">{totals.count}</p></div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">إجمالي المدين</p><p className="mt-1 text-2xl font-bold">{totals.debit.toLocaleString("ar-EG")}</p></div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm"><p className="text-sm text-muted-foreground">إجمالي الدائن</p><p className="mt-1 text-2xl font-bold">{totals.credit.toLocaleString("ar-EG")}</p></div>
      </section>
      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <label className="text-sm font-medium">الشركة<input type="number" min={1} value={companyId} onChange={(e) => setCompanyId(Number(e.target.value) || 0)} className="mt-1 w-28 rounded-lg border bg-background px-3 py-2" /></label>
          <label className="text-sm font-medium">الحالة<select value={statusFilter} onChange={e => setStatusFilter(e.target.value)} className="mt-1 w-40 rounded-lg border bg-background px-3 py-2"><option value="">كل الحالات</option>{Object.entries(statusLabels).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>
          <label className="text-sm font-medium">اليومية<select value={journalFilter} onChange={e => setJournalFilter(e.target.value)} className="mt-1 w-48 rounded-lg border bg-background px-3 py-2"><option value="">كل اليوميات</option>{journals.filter(j => j.is_active).map(j => <option key={j.id} value={j.id}>{j.code} — {j.name_ar}</option>)}</select></label>
          <label className="text-sm font-medium">من تاريخ<input type="date" value={fromDate} onChange={e => setFromDate(e.target.value)} className="mt-1 rounded-lg border bg-background px-3 py-2" /></label>
          <label className="text-sm font-medium">إلى تاريخ<input type="date" value={toDate} onChange={e => setToDate(e.target.value)} className="mt-1 rounded-lg border bg-background px-3 py-2" /></label>
          <button className="rounded-lg border px-3 py-2" onClick={() => void loadEntries()}>تطبيق</button>
          <button className="rounded-lg border px-3 py-2" onClick={() => { setStatusFilter(""); setJournalFilter(""); setFromDate(""); setToDate(""); setFilter(""); void setTimeout(() => void loadEntries(), 0); }}>مسح</button>
          <button className="rounded-lg bg-primary px-3 py-2 text-primary-foreground" onClick={() => setShowCreate(true)}>+ إنشاء مسودة</button>
          <input value={filter} onChange={(e) => setFilter(e.target.value)} placeholder="بحث داخل النتائج..." className="w-full max-w-xs rounded-lg border bg-background px-3 py-2" />
          <span className="text-sm text-muted-foreground">{loading ? "جاري التحميل..." : `${filtered.length} قيد`}</span>
        </div>
        {error && <div className="mb-4 rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1100px] text-sm">
            <thead><tr className="border-b text-right text-muted-foreground"><th className="p-3">رقم القيد</th><th className="p-3">التاريخ</th><th className="p-3">الوصف</th><th className="p-3">مدين</th><th className="p-3">دائن</th><th className="p-3">الحالة</th><th className="p-3">إجراءات</th></tr></thead>
            <tbody>
              {filtered.map((entry) => (
                <tr key={entry.id} className="border-b last:border-0">
                  <td className="p-3 font-medium">{entry.entry_number}</td><td className="p-3">{formatCompanyDate(entry.entry_date, dateFormat)}</td><td className="p-3">{entry.description}</td>
                  <td className="p-3">{Number(entry.total_debit).toLocaleString("ar-EG")}</td><td className="p-3">{Number(entry.total_credit).toLocaleString("ar-EG")}</td><td className="p-3">{statusLabels[entry.status] ?? entry.status}</td>
                  <td className="flex flex-wrap gap-2 p-3">
                    <button className="rounded-lg border px-2 py-1" disabled={detailsLoading} onClick={() => void openDetails(entry.id)}>{detailsLoading ? "تحميل..." : "عرض"}</button>
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
            <label className="text-sm font-medium">رقم الفرع<input type="number" min={1} required value={createForm.branchId} onChange={e => setCreateForm(v => ({...v,branchId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">اليومية
              <select required value={createForm.journalId} onChange={e => setCreateForm(v => ({...v,journalId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" disabled={optionsLoading}>
                <option value="">{optionsLoading ? "جاري التحميل..." : "اختر اليومية"}</option>
                {journals.filter(j => j.is_active && j.allow_manual_entries).map(j => <option key={j.id} value={j.id}>{j.code} — {j.name_ar}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium">رقم السنة المالية<input type="number" min={1} required value={createForm.fiscalYearId} onChange={e => setCreateForm(v => ({...v,fiscalYearId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">رقم الفترة<input type="number" min={1} required value={createForm.periodId} onChange={e => setCreateForm(v => ({...v,periodId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">حساب المدين
              <select required value={createForm.debitAccountId} onChange={e => setCreateForm(v => ({...v,debitAccountId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" disabled={optionsLoading}>
                <option value="">{optionsLoading ? "جاري التحميل..." : "اختر الحساب"}</option>
                {accounts.map(a => <option key={a.id} value={a.id}>{a.code} — {a.name_ar}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium">حساب الدائن
              <select required value={createForm.creditAccountId} onChange={e => setCreateForm(v => ({...v,creditAccountId:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" disabled={optionsLoading}>
                <option value="">{optionsLoading ? "جاري التحميل..." : "اختر الحساب"}</option>
                {accounts.map(a => <option key={a.id} value={a.id}>{a.code} — {a.name_ar}</option>)}
              </select>
            </label>
            <label className="text-sm font-medium">رقم القيد<input required value={createForm.entryNumber} onChange={e => setCreateForm(v => ({...v,entryNumber:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">التاريخ<input type="date" required value={createForm.entryDate} onChange={e => setCreateForm(v => ({...v,entryDate:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium">المبلغ<input type="number" min="0.01" step="0.01" required value={createForm.amount} onChange={e => setCreateForm(v => ({...v,amount:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <label className="text-sm font-medium sm:col-span-2 lg:col-span-3">الوصف<input required value={createForm.description} onChange={e => setCreateForm(v => ({...v,description:e.target.value}))} className="mt-1 w-full rounded-lg border bg-background px-3 py-2" /></label>
            <div className="flex gap-2 sm:col-span-2 lg:col-span-3"><button type="submit" disabled={createBusy} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground">{createBusy ? "جاري الإنشاء..." : "إنشاء المسودة"}</button><button type="button" className="rounded-lg border px-4 py-2" onClick={() => setShowCreate(false)}>إلغاء</button></div>
          </form>
          <p className="mt-3 text-xs text-muted-foreground">اليومية والحسابات تُحمّل تلقائيًا من الشركة النشطة. الفرع والسنة والفترة تُتحقق منها الخدمة قبل الحفظ.</p>
        </section>
      )}
      {details && (
        <section className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">تفاصيل القيد {details.entry_number}</h2><button className="rounded-lg border px-3 py-1" onClick={() => setDetails(null)}>إغلاق</button></div>
          <div className="grid gap-3 text-sm sm:grid-cols-2"><div>التاريخ: {formatCompanyDate(details.entry_date, dateFormat)}</div><div>الحالة: {statusLabels[details.status] ?? details.status}</div><div>الفرع: {details.branch_id}</div><div>الفترة: {details.period_id}</div><div>العملة: {details.currency_code ?? "EGP"}</div><div>مرجع: {details.reference || "—"}</div></div>
          <div className="mt-5 overflow-x-auto"><table className="w-full min-w-[850px] text-sm"><thead><tr className="border-b text-right text-muted-foreground"><th className="p-3">السطر</th><th className="p-3">الحساب</th><th className="p-3">الوصف</th><th className="p-3">مدين</th><th className="p-3">دائن</th></tr></thead><tbody>
            {(details.lines ?? []).map(line => <tr key={line.id} className="border-b last:border-0"><td className="p-3">{line.line_number}</td><td className="p-3">{accountName(line.account_combination_id)}</td><td className="p-3">{line.description || "—"}</td><td className="p-3">{Number(line.debit).toLocaleString("ar-EG")}</td><td className="p-3">{Number(line.credit).toLocaleString("ar-EG")}</td></tr>)}
          </tbody></table></div>
        </section>
      )}
    </div>
  );
}
