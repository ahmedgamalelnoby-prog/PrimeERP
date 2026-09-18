import { useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";

import PageHeader from "@/components/layout/PageHeader";



type Summary = {
  company_id: number;
  revenue: string;
  expenses: string;
  net_profit: string;
  assets: string;
  liabilities: string;
  equity: string;
};

type TrialRow = {
  account_combination_id: number;
  account_code: string;
  account_name: string;
  financial_statement: string;
  account_category: string;
  normal_balance: string;
  debit: string;
  credit: string;
  balance: string;
};

type TrialBalance = {
  company_id: number;
  from_date: string | null;
  to_date: string | null;
  rows: TrialRow[];
  total_debit: string;
  total_credit: string;
};

const formatMoney = (value: string | number) =>
  Number(value).toLocaleString("ar-EG", { maximumFractionDigits: 2 });

export default function FinancialReportsPage() {
  const [companyId, setCompanyId] = useState(() => {
    const n = Number(localStorage.getItem("company_id"));
    return Number.isInteger(n) && n > 0 ? n : 0;
  });
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [trialBalance, setTrialBalance] = useState<TrialBalance | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const query = useMemo(() => {
    const params = new URLSearchParams({ company_id: String(companyId) });
    if (fromDate) params.set("from_date", fromDate);
    if (toDate) params.set("to_date", toDate);
    return params.toString();
  }, [companyId, fromDate, toDate]);

  useEffect(() => {
    let active = true;
    if (!companyId) {
      setSummary(null);
      setTrialBalance(null);
      setLoading(false);
      setError("اختر شركة فعالة أولاً.");
      return;
    }
    if (fromDate && toDate && fromDate > toDate) {
      setError("تاريخ البداية يجب أن يكون قبل أو مساويًا لتاريخ النهاية.");
      return;
    }

    setLoading(true);
    setError(null);
    Promise.all([
      fetch(`${API_BASE}/accounting/reports/summary?${query}`),
      fetch(`${API_BASE}/accounting/reports/trial-balance?${query}`),
    ])
      .then(async ([summaryResponse, trialResponse]) => {
        if (!summaryResponse.ok) throw new Error((await summaryResponse.text()) || "تعذر تحميل الملخص المالي");
        if (!trialResponse.ok) throw new Error((await trialResponse.text()) || "تعذر تحميل ميزان المراجعة");
        return Promise.all([
          summaryResponse.json() as Promise<Summary>,
          trialResponse.json() as Promise<TrialBalance>,
        ]);
      })
      .then(([summaryData, trialData]) => {
        if (!active) return;
        setSummary(summaryData);
        setTrialBalance(trialData);
      })
      .catch((reason: unknown) => {
        if (!active) return;
        setSummary(null);
        setTrialBalance(null);
        setError(reason instanceof Error ? reason.message : "تعذر تحميل التقارير المالية");
      })
      .finally(() => active && setLoading(false));

    return () => {
      active = false;
    };
  }, [companyId, query, fromDate, toDate]);

  const cards = summary
    ? [
        ["الإيرادات", summary.revenue],
        ["المصروفات", summary.expenses],
        ["صافي الربح", summary.net_profit],
        ["الأصول", summary.assets],
        ["الخصوم", summary.liabilities],
        ["حقوق الملكية", summary.equity],
      ]
    : [];

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="التقارير المالية"
        description="ملخص مالي وميزان مراجعة مبنيان مباشرة على القيود المرحلة، مع نطاق زمني واضح."
      />

      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="grid gap-4 md:grid-cols-4 md:items-end">
          <label className="text-sm font-medium">
            الشركة
            <input
              type="number"
              min={1}
              value={companyId || ""}
              onChange={(event) => setCompanyId(Number(event.target.value) || 0)}
              className="mt-1 w-full rounded-lg border bg-background px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium">
            من تاريخ
            <input
              type="date"
              value={fromDate}
              onChange={(event) => setFromDate(event.target.value)}
              className="mt-1 w-full rounded-lg border bg-background px-3 py-2"
            />
          </label>
          <label className="text-sm font-medium">
            إلى تاريخ
            <input
              type="date"
              value={toDate}
              onChange={(event) => setToDate(event.target.value)}
              className="mt-1 w-full rounded-lg border bg-background px-3 py-2"
            />
          </label>
          <div className="text-sm text-muted-foreground">
            {loading ? "جاري التحديث..." : trialBalance ? `عدد الحسابات: ${trialBalance.rows.length}` : "لا توجد بيانات"}
          </div>
        </div>
      </section>

      {error && <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">{error}</div>}

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, value]) => (
          <div key={label} className="rounded-2xl border bg-card p-5 shadow-sm">
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="mt-2 text-2xl font-bold">{formatMoney(value)}</p>
          </div>
        ))}
      </section>

      {trialBalance && (
        <section className="rounded-2xl border bg-card shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 border-b p-4">
            <div>
              <h2 className="font-semibold">ميزان المراجعة</h2>
              <p className="text-sm text-muted-foreground">
                إجمالي المدين {formatMoney(trialBalance.total_debit)} — إجمالي الدائن {formatMoney(trialBalance.total_credit)}
              </p>
            </div>
            <span className="rounded-full border px-3 py-1 text-xs">{trialBalance.rows.length} حساب</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-right">
                  <th className="p-3">الحساب</th>
                  <th className="p-3">التصنيف</th>
                  <th className="p-3">مدين</th>
                  <th className="p-3">دائن</th>
                  <th className="p-3">الرصيد</th>
                </tr>
              </thead>
              <tbody>
                {trialBalance.rows.map((row) => (
                  <tr key={row.account_combination_id} className="border-b last:border-0">
                    <td className="p-3">
                      <div className="font-medium">{row.account_code}</div>
                      <div className="text-xs text-muted-foreground">{row.account_name}</div>
                    </td>
                    <td className="p-3">{row.account_category || row.financial_statement}</td>
                    <td className="p-3">{formatMoney(row.debit)}</td>
                    <td className="p-3">{formatMoney(row.credit)}</td>
                    <td className="p-3 font-medium">{formatMoney(row.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {!trialBalance.rows.length && <div className="p-8 text-center text-muted-foreground">لا توجد قيود مرحلة ضمن النطاق المحدد.</div>}
        </section>
      )}

      {!loading && !error && !summary && !trialBalance && (
        <div className="rounded-2xl border bg-card p-8 text-center text-muted-foreground">لا توجد بيانات مالية مرحّلة بعد.</div>
      )}
    </div>
  );
}
