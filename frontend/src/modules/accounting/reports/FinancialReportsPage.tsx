import { useEffect, useState } from "react";

import PageHeader from "@/components/layout/PageHeader";

const API_BASE = import.meta.env.VITE_API_URL ?? "/api/v1";

type Summary = {
  revenue: string;
  expenses: string;
  net_profit: string;
  assets: string;
  liabilities: string;
  equity: string;
};

const formatMoney = (value: string) => Number(value).toLocaleString("ar-EG", { maximumFractionDigits: 2 });

export default function FinancialReportsPage() {
  const [companyId, setCompanyId] = useState(() => { const n = Number(localStorage.getItem("company_id")); return Number.isInteger(n) && n > 0 ? n : 0; });
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!companyId) { setSummary(null); setLoading(false); setError("اختر شركة فعالة أولاً."); return; }
    setLoading(true);
    setError(null);
    fetch(`${API_BASE}/accounting/reports/summary?company_id=${companyId}`)
      .then(async (response) => {
        if (!response.ok) throw new Error((await response.text()) || "تعذر تحميل التقرير");
        return response.json() as Promise<Summary>;
      })
      .then((data) => active && setSummary(data))
      .catch((reason: unknown) => active && setError(reason instanceof Error ? reason.message : "تعذر تحميل التقرير"))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [companyId]);

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
        description="ملخص مالي مبني مباشرة على القيود المرحلة، بدون الاعتماد على بيانات العرض فقط."
      />

      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <label className="flex items-center gap-2 text-sm font-medium">
          الشركة
          <input
            type="number"
            min={1}
            value={companyId}
            onChange={(event) => setCompanyId(Number(event.target.value) || 0)}
            className="w-28 rounded-lg border bg-background px-3 py-2"
          />
          {loading && <span className="text-muted-foreground">جاري التحديث...</span>}
        </label>
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

      {!loading && !error && !summary && (
        <div className="rounded-2xl border bg-card p-8 text-center text-muted-foreground">لا توجد بيانات مالية مرحّلة بعد.</div>
      )}
    </div>
  );
}
