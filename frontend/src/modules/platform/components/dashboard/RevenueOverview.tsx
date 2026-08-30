import { revenueOverview } from "../../data/dashboard.data";

export default function RevenueOverview() {
  return (
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">
            الإيرادات والمصروفات
          </h2>

          <p className="mt-1 text-sm text-muted-foreground">
            الأداء المالي خلال آخر سبعة أشهر
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs">
          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-primary" />
            الإيرادات
          </span>

          <span className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-muted-foreground/40" />
            المصروفات
          </span>
        </div>
      </div>

      <div className="mt-8 flex h-72 items-end justify-between gap-3 border-b border-dashed px-2">
        {revenueOverview.map((point) => (
          <div
            key={point.month}
            className="flex h-full min-w-0 flex-1 flex-col items-center justify-end"
          >
            <div className="flex h-[230px] w-full max-w-14 items-end justify-center gap-1.5">
              <div
                className="w-2/5 rounded-t-md bg-primary transition-all hover:opacity-80"
                style={{ height: `${point.revenue}%` }}
                title={`الإيرادات: ${point.revenue}%`}
              />

              <div
                className="w-2/5 rounded-t-md bg-muted-foreground/40 transition-all hover:opacity-80"
                style={{ height: `${point.expenses}%` }}
                title={`المصروفات: ${point.expenses}%`}
              />
            </div>

            <span className="mt-3 truncate text-xs text-muted-foreground">
              {point.month}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
