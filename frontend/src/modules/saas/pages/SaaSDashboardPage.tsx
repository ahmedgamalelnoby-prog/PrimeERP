import { useEffect, useState } from "react";
import { Activity, ArrowLeft, Boxes, CircleDollarSign, Layers3, ShieldCheck, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { plansService } from "@/modules/platform/plans/plans.service";
import type { Plan } from "@/modules/platform/plans/plans.types";
import { saasEntitlementsService } from "../services/entitlements.service";

export default function SaaSDashboardPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [moduleCount, setModuleCount] = useState(0);

  useEffect(() => {
    Promise.all([plansService.list(), saasEntitlementsService.listModules()])
      .then(([planItems, modules]) => {
        setPlans(planItems);
        setModuleCount(modules.length);
      })
      .catch(() => {
        setPlans([]);
        setModuleCount(0);
      });
  }, []);

  const active = plans.filter((p) => p.status === "active");
  const publicPlans = active.filter((p) => p.is_public);

  return (
    <div className="mx-auto w-full max-w-[1500px] space-y-7" dir="rtl">
      <section className="overflow-hidden rounded-[28px] bg-gradient-to-l from-[#063f9f] via-[#0968d7] to-[#21a8ef] p-7 text-white shadow-xl shadow-blue-900/10 md:p-9">
        <div className="flex flex-col justify-between gap-7 lg:flex-row lg:items-end">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold"><Sparkles className="h-4 w-4" /> SaaS Platform</span>
            <h1 className="mt-4 text-3xl font-black md:text-4xl">مركز إدارة PrimeERP SaaS</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-blue-50/90">
              نقطة التحكم المركزية للباقات، الموديولات، حدود الاستخدام والاستحقاقات. كل تغيير هنا مصمم ليصل إلى دورة الـTenant والاشتراك الفعلية.
            </p>
          </div>
          <Link to="/platform/plans" className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-black text-blue-700 shadow-sm hover:bg-blue-50">
            إدارة الباقات والاستحقاقات <ArrowLeft className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "الباقات النشطة", value: active.length, icon: Layers3 },
          { label: "الباقات العامة", value: publicPlans.length, icon: CircleDollarSign },
          { label: "كتالوج الموديولات", value: moduleCount, icon: Boxes },
          { label: "الاستحقاقات", value: "Live", icon: ShieldCheck },
        ].map(({ label, value, icon: Icon }) => (
          <article key={label} className="rounded-2xl border bg-card p-5 shadow-sm">
            <div className="flex items-start justify-between"><span className="text-sm text-slate-500">{label}</span><span className="rounded-xl bg-blue-50 p-2.5 text-blue-600"><Icon className="h-5 w-5" /></span></div>
            <p className="mt-4 text-3xl font-black text-slate-900">{value}</p>
            <p className="mt-1 text-xs text-slate-400">من الكتالوج الحالي</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        <div className="rounded-[24px] border bg-card p-6 shadow-sm">
          <div className="flex items-center justify-between border-b pb-4">
            <div><p className="text-xs font-bold uppercase tracking-wider text-blue-600">Pricing catalog</p><h2 className="mt-1 text-xl font-black">خطط الأسعار</h2></div>
            <CircleDollarSign className="h-6 w-6 text-blue-600" />
          </div>
          <div className="mt-5 space-y-3">
            {plans.map((plan) => (
              <Link key={plan.id} to="/platform/plans" className="flex items-center justify-between rounded-2xl border p-4 transition hover:border-blue-300 hover:bg-blue-50/50">
                <div><b className="block">{plan.name_ar || plan.name}</b><span className="text-xs text-slate-400">{plan.code} · {plan.status}</span></div>
                <div className="text-left"><b className="block">{new Intl.NumberFormat("ar-EG").format(plan.monthly_price)} {plan.currency}</b><span className="text-xs text-slate-400">شهريًا</span></div>
              </Link>
            ))}
          </div>
        </div>

        <div className="rounded-[24px] border bg-slate-950 p-6 text-white shadow-sm">
          <div className="flex items-center gap-3"><Activity className="h-5 w-5 text-cyan-300" /><h2 className="text-xl font-black">SaaS Architecture</h2></div>
          <div className="mt-6 space-y-3 text-sm">
            {["Plan Catalog", "Plan → Module Entitlements", "Plan → Usage Limits", "Tenant → Subscription", "Subscription → Access Enforcement"].map((item, i) => (
              <div key={item} className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-3"><span className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-500/20 text-xs font-black text-cyan-300">{i + 1}</span><span>{item}</span></div>
            ))}
          </div>
          <div className="mt-5 rounded-2xl bg-blue-500/15 p-4 text-xs leading-6 text-blue-100">
            الهدف: لا توجد باقة “للشكل فقط”. الباقة هي عقد تجاري يحدد السعر، الحدود، الموديولات والاستحقاقات التي يعتمد عليها الـTenant فعليًا.
          </div>
        </div>
      </section>
    </div>
  );
}
