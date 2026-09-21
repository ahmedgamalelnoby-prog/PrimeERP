import type { BusinessUnit } from "../../types/dashboard.types";
import { businessUnits as fallbackUnits } from "../../data/dashboard.data";

export default function BusinessUnitsSummary({ items = fallbackUnits }: { items?: BusinessUnit[] }) {
  return (
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div><h2 className="text-lg font-semibold">ملخص المؤسسة</h2><p className="mt-1 text-sm text-muted-foreground">بيانات حية مرتبطة بمساحة العمل الحالية</p></div>
      <div className="mt-5 space-y-3">{items.map((unit) => { const Icon = unit.icon; return <div key={unit.id} className="flex items-center justify-between rounded-xl border p-4"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted text-foreground"><Icon className="h-5 w-5" /></div><span className="text-sm font-medium">{unit.title}</span></div><span className="text-xl font-bold">{unit.value}</span></div>; })}</div>
    </section>
  );
}
