import { useEffect, useState } from "react";

import { plansService } from "./plans.service";
import type { Plan } from "./plans.types";

function formatPrice(value: number, currency: string) {
  return new Intl.NumberFormat("ar-EG", { maximumFractionDigits: 2 }).format(value) + ` ${currency}`;
}

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    plansService
      .list()
      .then((items) => mounted && setPlans(items))
      .catch((err: unknown) => mounted && setError(err instanceof Error ? err.message : "تعذر تحميل الباقات"))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">باقات PrimeERP</h1>
        <p className="mt-1 text-sm text-muted-foreground">إدارة الباقات والأسعار وفترة التجربة.</p>
      </header>

      {loading && <div className="rounded-xl border p-6">جاري تحميل الباقات...</div>}
      {error && <div className="rounded-xl border p-6 text-destructive">{error}</div>}

      {!loading && !error && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {plans.map((plan) => (
            <article key={plan.id} className="rounded-2xl border bg-card p-5 shadow-sm">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold">{plan.name_ar || plan.display_name || plan.name}</h2>
                  <p className="text-xs text-muted-foreground">{plan.code} · v{plan.version}</p>
                </div>
                <span className="rounded-full border px-2 py-1 text-xs">{plan.status}</span>
              </div>
              {plan.description && <p className="mt-4 text-sm text-muted-foreground">{plan.description}</p>}
              <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl border p-3"><span className="text-muted-foreground">شهري</span><div className="font-semibold">{formatPrice(plan.monthly_price, plan.currency)}</div></div>
                <div className="rounded-xl border p-3"><span className="text-muted-foreground">سنوي</span><div className="font-semibold">{formatPrice(plan.yearly_price, plan.currency)}</div></div>
              </div>
              <div className="mt-4 flex justify-between text-xs text-muted-foreground">
                <span>تجربة: {plan.trial_days} يوم</span>
                <span>{plan.is_default ? "الباقة الافتراضية" : plan.plan_type}</span>
              </div>
            </article>
          ))}
          {plans.length === 0 && <div className="rounded-xl border p-6 text-muted-foreground">لا توجد باقات معرفة حاليًا.</div>}
        </div>
      )}
    </section>
  );
}
