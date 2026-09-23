import { useEffect, useMemo, useState } from "react";
import {
  Check,
  CircleDollarSign,
  Crown,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Users,
  Boxes,
  ToggleLeft,
  ToggleRight,
} from "lucide-react";

import { plansService } from "./plans.service";
import type { Plan } from "./plans.types";
import { saasEntitlementsService } from "@/modules/saas/services/entitlements.service";
import type { Sasmodule } from "@/modules/saas/api/entitlements.api";

function formatPrice(value: number, currency: string) {
  return new Intl.NumberFormat("ar-EG", { maximumFractionDigits: 2 }).format(value) + ` ${currency}`;
}

const planAccent: Record<string, string> = {
  trial: "from-sky-500 to-cyan-500",
  starter: "from-blue-600 to-sky-500",
  professional: "from-indigo-600 to-blue-500",
  enterprise: "from-slate-800 to-slate-600",
};

export default function PlansPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [modules, setModules] = useState<Sasmodule[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<Plan | null>(null);
  const [planModules, setPlanModules] = useState<Sasmodule[]>([]);
  const [loading, setLoading] = useState(true);
  const [moduleLoading, setModuleLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savingModule, setSavingModule] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [planItems, moduleItems] = await Promise.all([
        plansService.list(),
        saasEntitlementsService.listModules(),
      ]);
      setPlans(planItems);
      setModules(moduleItems);
      const defaultPlan = planItems.find((plan) => plan.is_default && plan.status === "active")
        ?? planItems.find((plan) => plan.status === "active")
        ?? planItems[0]
        ?? null;
      setSelectedPlan(defaultPlan);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "تعذر تحميل كتالوج SaaS");
    } finally {
      setLoading(false);
    }
  };

  const loadPlanModules = async (plan: Plan) => {
    setModuleLoading(true);
    try {
      setPlanModules(await saasEntitlementsService.listPlanModules(plan.id));
    } finally {
      setModuleLoading(false);
    }
  };

  useEffect(() => { void load(); }, []);
  useEffect(() => {
    if (selectedPlan) void loadPlanModules(selectedPlan);
  }, [selectedPlan]);

  const enabledCount = useMemo(
    () => planModules.filter((module) => module.is_enabled).length,
    [planModules],
  );

  const toggleModule = async (module: Sasmodule) => {
    if (!selectedPlan || savingModule === module.module_id) return;
    setSavingModule(module.module_id);
    try {
      await saasEntitlementsService.setPlanModule(
        selectedPlan.id,
        module.module_id,
        !module.is_enabled,
      );
      await loadPlanModules(selectedPlan);
    } finally {
      setSavingModule(null);
    }
  };

  return (
    <div className="mx-auto w-full max-w-[1500px] space-y-8" dir="rtl">
      <header className="relative overflow-hidden rounded-[28px] bg-gradient-to-l from-[#0757d9] via-[#1478e8] to-[#27b4f2] p-7 text-white shadow-xl shadow-blue-900/10 md:p-9">
        <div className="absolute -left-16 -top-24 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold">
              <Sparkles className="h-4 w-4" /> PrimeERP SaaS Control Center
            </div>
            <h1 className="text-3xl font-black tracking-tight md:text-4xl">الباقات والاشتراكات والاستحقاقات</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-blue-50/90">
              إدارة الباقات الفعلية، حدود الاستخدام، والموديولات المفعلة لكل باقة من مصدر واحد مرتبط مباشرة بمنظومة SaaS.
            </p>
          </div>
          <button onClick={() => void load()} className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/20 bg-white/10 px-4 py-2.5 text-sm font-bold hover:bg-white/15">
            <RefreshCw className="h-4 w-4" /> تحديث الكتالوج
          </button>
        </div>
      </header>

      {error && <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{error}</div>}

      {loading ? (
        <div className="flex min-h-56 items-center justify-center rounded-2xl border bg-card">
          <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
        </div>
      ) : (
        <>
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {plans.map((plan) => {
              const active = plan.status === "active";
              const selected = selectedPlan?.id === plan.id;
              const accent = planAccent[plan.code] ?? "from-blue-600 to-cyan-500";
              return (
                <button
                  key={plan.id}
                  type="button"
                  onClick={() => setSelectedPlan(plan)}
                  className={`group relative overflow-hidden rounded-[24px] border bg-card p-6 text-right shadow-sm transition hover:-translate-y-0.5 hover:shadow-lg ${selected ? "border-blue-500 ring-2 ring-blue-100" : "border-slate-200"}`}
                >
                  {plan.is_default && <span className="absolute left-4 top-4 rounded-full bg-blue-50 px-2.5 py-1 text-[10px] font-black text-blue-700">DEFAULT</span>}
                  <div className={`mb-5 h-1.5 w-16 rounded-full bg-gradient-to-l ${accent}`} />
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-wider text-slate-400">{plan.code} · v{plan.version}</p>
                      <h2 className="mt-1 text-2xl font-black text-slate-900">{plan.name_ar || plan.display_name || plan.name}</h2>
                    </div>
                    <span className={`rounded-full px-2.5 py-1 text-[11px] font-bold ${active ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}`}>
                      {active ? "Active" : plan.status}
                    </span>
                  </div>
                  <div className="mt-6 flex items-end justify-between">
                    <div>
                      <p className="text-3xl font-black text-slate-900">{formatPrice(plan.monthly_price, plan.currency)}</p>
                      <p className="mt-1 text-xs text-slate-400">شهريًا · سنوي {formatPrice(plan.yearly_price, plan.currency)}</p>
                    </div>
                    <Crown className="h-7 w-7 text-blue-500" />
                  </div>
                  <div className="mt-5 grid grid-cols-3 gap-2 text-xs">
                    <div className="rounded-xl bg-slate-50 p-3"><Users className="mb-1 h-4 w-4 text-blue-600" /><b>{plan.max_users ?? "∞"}</b><span className="mr-1 text-slate-400">Users</span></div>
                    <div className="rounded-xl bg-slate-50 p-3"><Boxes className="mb-1 h-4 w-4 text-blue-600" /><b>{plan.max_products ?? "∞"}</b><span className="mr-1 text-slate-400">Items</span></div>
                    <div className="rounded-xl bg-slate-50 p-3"><ShieldCheck className="mb-1 h-4 w-4 text-blue-600" /><b>{plan.trial_days}</b><span className="mr-1 text-slate-400">Trial</span></div>
                  </div>
                </button>
              );
            })}
          </section>

          {plans.length === 0 && (
            <div className="rounded-2xl border border-dashed p-10 text-center text-slate-500">لا توجد باقات. تم تشغيل مزامنة كتالوج SaaS، أعد التحديث.</div>
          )}

          {selectedPlan && (
            <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
              <div className="rounded-[24px] border bg-card p-6 shadow-sm">
                <div className="flex flex-col justify-between gap-4 border-b pb-5 md:flex-row md:items-center">
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-blue-600">Entitlements</p>
                    <h2 className="mt-1 text-xl font-black">موديولات الباقة: {selectedPlan.name_ar || selectedPlan.name}</h2>
                    <p className="mt-1 text-sm text-slate-500">{enabledCount} من {modules.length} موديول مفعّل — التغيير ينعكس على صلاحيات الباقة في الـSaaS.</p>
                  </div>
                  <div className="rounded-xl bg-blue-50 px-4 py-2 text-sm font-bold text-blue-700">{enabledCount} Enabled</div>
                </div>
                <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {(planModules.length ? planModules : modules).map((module) => (
                    <button
                      key={module.module_id}
                      type="button"
                      onClick={() => void toggleModule(module)}
                      disabled={moduleLoading || savingModule === module.module_id}
                      className={`flex items-center justify-between gap-3 rounded-2xl border p-4 text-right transition ${module.is_enabled ? "border-blue-200 bg-blue-50/60" : "border-slate-200 bg-slate-50"} disabled:opacity-60`}
                    >
                      <span className="flex min-w-0 items-center gap-3">
                        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${module.is_enabled ? "bg-blue-600 text-white" : "bg-white text-slate-400"}`}>
                          <Boxes className="h-5 w-5" />
                        </span>
                        <span className="min-w-0">
                          <span className="block truncate font-bold text-slate-800">{module.name_ar || module.name_en || module.code}</span>
                          <span className="block text-[11px] text-slate-400">{module.code}{module.is_core ? " · Core" : ""}</span>
                        </span>
                      </span>
                      {savingModule === module.module_id ? <Loader2 className="h-5 w-5 animate-spin text-blue-600" /> : module.is_enabled ? <ToggleRight className="h-7 w-7 text-blue-600" /> : <ToggleLeft className="h-7 w-7 text-slate-400" />}
                    </button>
                  ))}
                </div>
              </div>

              <aside className="rounded-[24px] border bg-slate-950 p-6 text-white shadow-lg">
                <p className="text-xs font-bold uppercase tracking-wider text-blue-300">Plan Contract</p>
                <h3 className="mt-2 text-xl font-black">{selectedPlan.name_ar || selectedPlan.name}</h3>
                <div className="mt-5 space-y-3 text-sm">
                  {[
                    ["Users", selectedPlan.max_users ?? "Unlimited"],
                    ["Companies", selectedPlan.max_companies ?? "Unlimited"],
                    ["Branches", selectedPlan.max_branches ?? "Unlimited"],
                    ["Products", selectedPlan.max_products ?? "Unlimited"],
                    ["Integrations", selectedPlan.max_integrations ?? "Unlimited"],
                    ["Storage", selectedPlan.storage_limit_mb ? `${selectedPlan.storage_limit_mb} MB` : "Unlimited"],
                  ].map(([label, value]) => (
                    <div key={String(label)} className="flex items-center justify-between border-b border-white/10 pb-3">
                      <span className="text-slate-400">{label}</span><b>{String(value)}</b>
                    </div>
                  ))}
                </div>
                <div className="mt-6 rounded-2xl bg-blue-500/15 p-4 text-xs leading-6 text-blue-100">
                  <Check className="mb-2 h-4 w-4 text-cyan-300" />
                  الباقة هنا مرتبطة بكتالوج SaaS الفعلي. الـTenant subscriptions القديمة تستمر في العمل، بينما واجهة Platform تستخدم الـcanonical plan catalog.
                </div>
              </aside>
            </section>
          )}
        </>
      )}
    </div>
  );
}
