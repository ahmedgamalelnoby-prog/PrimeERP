import { useEffect, useState } from "react";
import client from "@/shared/api/client";
import { useAuth } from "@/modules/identity";

interface Dashboard {
  total: number; trial: number; active: number; expired: number; suspended: number;
  pending_payments: number; paid_revenue: string | number;
}

interface Trial {
  id: number; name: string; owner_name: string; email: string; status: string;
  trial_started_at: string | null; trial_ends_at: string | null; plan_code: string | null;
}

interface Payment { id: number; tenant_name: string; amount: string | number; currency_code: string; status: string; reference?: string; }

export default function SaaSPlatformAdminPage() {
  const { user } = useAuth();
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [trials, setTrials] = useState<Trial[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [trialDays, setTrialDays] = useState("14");
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const [d, t, p, s] = await Promise.all([
        client.get<Dashboard>("/platform/saas/dashboard"),
        client.get<{ items: Trial[] }>("/platform/saas/trials"),
        client.get<{ items: Payment[] }>("/platform/saas/payments?status=pending"),
        client.get<{ items: { key: string; value: string }[] }>("/platform/saas/settings"),
      ]);
      setDashboard(d.data);
      setTrials(t.data.items);
      setPayments(p.data.items);
      const setting = s.data.items.find((x) => x.key === "default_trial_days");
      if (setting) setTrialDays(setting.value);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { if (user?.is_platform_admin) void load(); }, [user?.is_platform_admin]);

  if (!user?.is_platform_admin) {
    return <div className="p-8 text-center" dir="rtl">ليس لديك صلاحية الدخول إلى إدارة المنصة.</div>;
  }

  const updateTrialDays = async () => {
    await client.put("/platform/saas/settings/default_trial_days", {
      value: trialDays, description: "Default free trial duration in days", is_public: false,
    });
    setMessage("تم تحديث مدة التجربة المجانية");
  };

  const approve = async (id: number) => {
    await client.post(`/platform/saas/payments/${id}/approve`, { duration_days: 365 });
    setMessage("تم اعتماد الدفع وتفعيل الاشتراك");
    await load();
  };

  const expire = async () => {
    const response = await client.post<{ updated: number }>("/platform/saas/maintenance/expire");
    setMessage(`تمت مراجعة ${response.data.updated} اشتراك`);
    await load();
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6" dir="rtl">
      <div className="mx-auto max-w-7xl space-y-6">
        <div>
          <p className="text-sm text-slate-500">PrimeERP Platform</p>
          <h1 className="text-3xl font-bold text-slate-900">إدارة SaaS والمنصة</h1>
          <p className="mt-1 text-slate-600">العملاء، التجارب، الاشتراكات، الباقات، الدفع والأسعار من مكان واحد.</p>
        </div>

        {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-emerald-800">{message}</div>}

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[['إجمالي العملاء', dashboard?.total ?? 0], ['تجريبي', dashboard?.trial ?? 0], ['نشط', dashboard?.active ?? 0], ['منتهي', dashboard?.expired ?? 0]].map(([label, value]) => (
            <div key={String(label)} className="rounded-2xl border bg-white p-5 shadow-sm">
              <div className="text-sm text-slate-500">{label}</div>
              <div className="mt-2 text-3xl font-bold">{value}</div>
            </div>
          ))}
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="rounded-2xl border bg-white p-5 shadow-sm lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">العملاء التجريبيون</h2>
              <span className="rounded-full bg-amber-100 px-3 py-1 text-sm text-amber-800">{trials.length}</span>
            </div>
            {loading ? <p>جاري التحميل...</p> : (
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="border-b text-right text-slate-500"><th className="p-3">الشركة</th><th className="p-3">المسؤول</th><th className="p-3">البريد</th><th className="p-3">النهاية</th><th className="p-3">الحالة</th></tr></thead>
                  <tbody>{trials.map((t) => <tr key={t.id} className="border-b last:border-0"><td className="p-3 font-medium">{t.name}</td><td className="p-3">{t.owner_name}</td><td className="p-3">{t.email}</td><td className="p-3">{t.trial_ends_at ? new Date(t.trial_ends_at).toLocaleDateString("ar-EG") : "—"}</td><td className="p-3">{t.status}</td></tr>)}</tbody>
                </table>
              </div>
            )}
          </section>

          <section className="rounded-2xl border bg-white p-5 shadow-sm">
            <h2 className="text-xl font-bold">إعدادات التجربة</h2>
            <label className="mt-5 block text-sm font-medium">مدة التجربة بالأيام</label>
            <input value={trialDays} onChange={(e) => setTrialDays(e.target.value)} type="number" min={1} max={365} className="mt-2 w-full rounded-xl border p-3" />
            <button onClick={() => void updateTrialDays()} className="mt-3 w-full rounded-xl bg-slate-900 p-3 font-semibold text-white">حفظ</button>
            <button onClick={() => void expire()} className="mt-3 w-full rounded-xl border p-3 font-semibold">فحص الاشتراكات المنتهية</button>
            <div className="mt-5 rounded-xl bg-slate-50 p-4 text-sm">الدخل المحصل: <b>{dashboard?.paid_revenue ?? 0}</b></div>
          </section>
        </div>

        <section className="rounded-2xl border bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-bold">طلبات الدفع</h2><span className="rounded-full bg-blue-100 px-3 py-1 text-sm">{payments.length}</span></div>
          <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
            {payments.map((p) => <div key={p.id} className="rounded-xl border p-4"><div className="font-semibold">{p.tenant_name}</div><div className="mt-1 text-sm text-slate-500">{p.amount} {p.currency_code}</div><div className="mt-1 text-xs text-slate-500">{p.reference || "بدون مرجع"}</div><button onClick={() => void approve(p.id)} className="mt-3 w-full rounded-lg bg-emerald-600 p-2 text-white">اعتماد وتفعيل سنة</button></div>)}
            {!payments.length && <p className="text-slate-500">لا توجد طلبات دفع معلقة.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}
