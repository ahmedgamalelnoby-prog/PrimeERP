import { Link } from "react-router-dom";

const areas = [
  ["دليل الحسابات", "/accounting/chart-of-accounts", "الحسابات والأقسام ومراكز التكلفة"],
  ["القيود اليومية", "/accounting/journal-entries", "إنشاء ومراجعة وترحيل القيود"],
  ["التقارير المالية", "/accounting/reports", "التقارير والتحليلات المالية"],
];

export default function AccountingPage() {
  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">المحاسبة والمالية</h1>
        <p className="mt-1 text-sm text-muted-foreground">مركز العمليات المالية في PrimeERP.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-3">
        {areas.map(([title, href, description]) => (
          <Link key={href} to={href} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md">
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
