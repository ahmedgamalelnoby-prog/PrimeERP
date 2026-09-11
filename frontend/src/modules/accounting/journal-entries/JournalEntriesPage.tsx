import { useEffect, useMemo, useState } from "react";

import PageHeader from "@/components/layout/PageHeader";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

type JournalEntry = {
  id: number;
  company_id: number;
  journal_id: number;
  entry_number: string;
  entry_date: string;
  posting_date: string | null;
  description: string;
  total_debit: string;
  total_credit: string;
  status: string;
};

const statusLabels: Record<string, string> = {
  draft: "مسودة",
  pending: "بانتظار الاعتماد",
  approved: "معتمد",
  posted: "مرحّل",
  cancelled: "ملغي",
  reversed: "معكوس",
};

async function loadEntries(companyId: number): Promise<JournalEntry[]> {
  const response = await fetch(
    `${API_BASE}/accounting/journal-entries?company_id=${companyId}`,
    { headers: { "Content-Type": "application/json" } },
  );
  if (!response.ok) {
    throw new Error((await response.text()) || "تعذر تحميل القيود اليومية");
  }
  return response.json() as Promise<JournalEntry[]>;
}

export default function JournalEntriesPage() {
  const [companyId, setCompanyId] = useState(1);
  const [entries, setEntries] = useState<JournalEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const totals = useMemo(
    () => ({
      count: entries.length,
      debit: entries.reduce((sum, entry) => sum + Number(entry.total_debit), 0),
      credit: entries.reduce((sum, entry) => sum + Number(entry.total_credit), 0),
    }),
    [entries],
  );

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    loadEntries(companyId)
      .then((data) => {
        if (active) setEntries(data);
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "تعذر تحميل البيانات");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [companyId]);

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="القيود اليومية"
        description="متابعة القيود ودورة المسودة والاعتماد والترحيل من نفس المحرك المحاسبي."
      />

      <section className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <p className="text-sm text-muted-foreground">عدد القيود</p>
          <p className="mt-1 text-2xl font-bold">{totals.count}</p>
        </div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <p className="text-sm text-muted-foreground">إجمالي المدين</p>
          <p className="mt-1 text-2xl font-bold">{totals.debit.toLocaleString("ar-EG")}</p>
        </div>
        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <p className="text-sm text-muted-foreground">إجمالي الدائن</p>
          <p className="mt-1 text-2xl font-bold">{totals.credit.toLocaleString("ar-EG")}</p>
        </div>
      </section>

      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-sm font-medium">
            الشركة
            <input
              type="number"
              min={1}
              value={companyId}
              onChange={(event) => setCompanyId(Number(event.target.value) || 1)}
              className="w-28 rounded-lg border bg-background px-3 py-2"
            />
          </label>
          <span className="text-sm text-muted-foreground">
            {loading ? "جاري التحميل..." : `${entries.length} قيد`}
          </span>
        </div>

        {error ? (
          <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-sm">
              <thead>
                <tr className="border-b text-right text-muted-foreground">
                  <th className="p-3">رقم القيد</th>
                  <th className="p-3">التاريخ</th>
                  <th className="p-3">الوصف</th>
                  <th className="p-3">مدين</th>
                  <th className="p-3">دائن</th>
                  <th className="p-3">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} className="border-b last:border-0">
                    <td className="p-3 font-medium">{entry.entry_number}</td>
                    <td className="p-3">{entry.entry_date}</td>
                    <td className="p-3">{entry.description}</td>
                    <td className="p-3">{Number(entry.total_debit).toLocaleString("ar-EG")}</td>
                    <td className="p-3">{Number(entry.total_credit).toLocaleString("ar-EG")}</td>
                    <td className="p-3">{statusLabels[entry.status] ?? entry.status}</td>
                  </tr>
                ))}
                {!loading && entries.length === 0 && (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-muted-foreground">
                      لا توجد قيود لهذه الشركة حتى الآن.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
