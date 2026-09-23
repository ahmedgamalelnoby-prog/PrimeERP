import { useEffect, useMemo, useState } from "react";
import { Bell, Building2, CheckCircle2, ChevronLeft, Clock3, CreditCard, Globe2, KeyRound, Languages, Loader2, LockKeyhole, Save, ShieldCheck, SlidersHorizontal, Users, WalletCards, Boxes } from "lucide-react";
import { Link } from "react-router-dom";
import toast from "react-hot-toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/modules/identity/hooks/useAuth";
import { settingsApi, type TenantSettings } from "../api/settings.api";

const moduleNames: Record<string, string> = { dashboard:"لوحة التحكم", accounting:"المحاسبة", sales:"المبيعات", purchasing:"المشتريات", inventory:"المخزون", crm:"CRM", pos:"POS", shipping:"الشحن", manufacturing:"التصنيع", reports:"التقارير", hospitality:"الفنادق والضيافة", commercial_leasing:"الإيجارات التجارية" };
const businessLabels: Record<string, string> = { restaurant:"مطعم", cafe:"كافيه", retail:"تجزئة", fashion:"ملابس وأزياء", perfume:"عطور", supermarket:"سوبر ماركت", pharmacy:"صيدلية", manufacturing:"تصنيع", services:"خدمات", other:"أعمال عامة" };

export default function SettingsPage() {
  const { user, refreshUser } = useAuth();
  const [settings, setSettings] = useState<TenantSettings | null>(null);
  const [form, setForm] = useState({ name:"", phone:"", business_type:"other", default_language:"ar" as "ar"|"en", default_locale:"ar-EG", timezone:"Africa/Cairo", currency_code:"EGP" });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    settingsApi.get().then((data) => {
      setSettings(data);
      setForm({ name:data.name, phone:data.phone ?? "", business_type:data.business_type, default_language:data.default_language, default_locale:data.default_locale, timezone:data.timezone, currency_code:data.currency_code });
    }).catch(() => toast.error("تعذر تحميل إعدادات مساحة العمل")).finally(() => setLoading(false));
  }, []);

  const enabledModules = useMemo(() => (user?.enabled_modules ?? []).filter((code) => !["dashboard","users","companies","branches"].includes(code)), [user?.enabled_modules]);

  const save = async () => {
    try {
      setSaving(true);
      const updated = await settingsApi.update(form);
      setSettings(updated);
      await refreshUser();
      toast.success("تم حفظ إعدادات الشركة بنجاح");
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? "تعذر حفظ الإعدادات");
    } finally { setSaving(false); }
  };

  if (loading) return <div className="flex min-h-[60vh] items-center justify-center"><Loader2 className="size-7 animate-spin text-blue-600" /></div>;

  return <div className="mx-auto w-full max-w-[1500px] space-y-6" dir="rtl">
    <section className="overflow-hidden rounded-[28px] bg-gradient-to-l from-[#071d49] via-[#0968d7] to-[#21a8ef] p-7 text-white shadow-xl md:p-9">
      <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
        <div><span className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-xs font-bold"><SlidersHorizontal className="size-4" /> مركز التحكم</span><h1 className="mt-4 text-3xl font-black md:text-4xl">إعدادات مساحة العمل</h1><p className="mt-3 max-w-3xl text-sm leading-7 text-blue-50/90">كل إعدادات العميل الأساسية في مكان واحد: بيانات الشركة، اللغة، المنطقة، العملة، الأمان، المستخدمون، الموديولات والاشتراك.</p></div>
        <div className="rounded-2xl border border-white/15 bg-white/10 px-5 py-4 backdrop-blur"><div className="text-xs text-blue-100">مساحة العمل</div><div className="mt-1 text-xl font-black">{settings?.name || user?.tenant_name || "—"}</div><div className="mt-1 text-xs text-blue-100/70">{settings?.slug || user?.tenant_slug || "—"}</div></div>
      </div>
    </section>

    <div className="grid gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,0.75fr)]">
      <main className="space-y-6">
        <section className="rounded-[24px] border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3 border-b pb-5"><span className="flex size-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Building2 className="size-5" /></span><div><h2 className="text-xl font-black">بيانات الشركة</h2><p className="text-sm text-muted-foreground">البيانات التي تظهر في مساحة العمل ولوحة التحكم.</p></div></div>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div className="space-y-2 md:col-span-2"><Label>اسم الشركة</Label><Input value={form.name} onChange={(e) => setForm((v) => ({...v,name:e.target.value}))} className="h-11 rounded-xl" /></div>
            <div className="space-y-2"><Label>البريد الإلكتروني</Label><Input value={settings?.email ?? ""} disabled className="h-11 rounded-xl bg-slate-50" /></div>
            <div className="space-y-2"><Label>رقم الهاتف</Label><Input value={form.phone} onChange={(e) => setForm((v) => ({...v,phone:e.target.value}))} className="h-11 rounded-xl" /></div>
            <div className="space-y-2"><Label>مجال النشاط</Label><select value={form.business_type} onChange={(e) => setForm((v) => ({...v,business_type:e.target.value}))} className="h-11 w-full rounded-xl border bg-background px-3 text-sm">{Object.entries(businessLabels).map(([key,label]) => <option key={key} value={key}>{label}</option>)}</select></div>
            <div className="space-y-2"><Label>الدولة</Label><Input value={settings?.country_code ?? "EG"} disabled className="h-11 rounded-xl bg-slate-50" /></div>
          </div>
        </section>

        <section className="rounded-[24px] border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3 border-b pb-5"><span className="flex size-11 items-center justify-center rounded-xl bg-cyan-50 text-cyan-700"><Globe2 className="size-5" /></span><div><h2 className="text-xl font-black">اللغة والمنطقة</h2><p className="text-sm text-muted-foreground">اللغة الافتراضية، المنطقة الزمنية والعملة.</p></div></div>
          <div className="mt-5 grid gap-5 md:grid-cols-2">
            <div className="space-y-2"><Label>لغة النظام</Label><select value={form.default_language} onChange={(e) => setForm((v) => ({...v,default_language:e.target.value as "ar"|"en"}))} className="h-11 w-full rounded-xl border bg-background px-3 text-sm"><option value="ar">العربية</option><option value="en">English</option></select></div>
            <div className="space-y-2"><Label>Locale</Label><Input value={form.default_locale} onChange={(e) => setForm((v) => ({...v,default_locale:e.target.value}))} className="h-11 rounded-xl" /></div>
            <div className="space-y-2"><Label>المنطقة الزمنية</Label><Input value={form.timezone} onChange={(e) => setForm((v) => ({...v,timezone:e.target.value}))} className="h-11 rounded-xl" /></div>
            <div className="space-y-2"><Label>العملة</Label><Input value={form.currency_code} maxLength={3} onChange={(e) => setForm((v) => ({...v,currency_code:e.target.value.toUpperCase()}))} className="h-11 rounded-xl" /></div>
          </div>
          <Button onClick={save} disabled={saving} className="mt-6 rounded-xl">{saving ? <Loader2 className="me-2 size-4 animate-spin" /> : <Save className="me-2 size-4" />}حفظ التغييرات</Button>
        </section>

        <section className="rounded-[24px] border bg-card p-6 shadow-sm">
          <div className="flex items-center gap-3"><span className="flex size-11 items-center justify-center rounded-xl bg-emerald-50 text-emerald-700"><Boxes className="size-5" /></span><div><h2 className="text-xl font-black">الموديولات المفعّلة</h2><p className="text-sm text-muted-foreground">القائمة تعكس استحقاقات الباقة الحالية ولا يمكن للعميل فتح موديول غير مفعّل.</p></div></div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{enabledModules.length ? enabledModules.map((code) => <div key={code} className="flex items-center gap-3 rounded-2xl border bg-slate-50 p-4"><CheckCircle2 className="size-5 text-emerald-600" /><span className="text-sm font-bold">{moduleNames[code] ?? code}</span></div>) : <div className="rounded-2xl bg-slate-50 p-4 text-sm text-slate-500">لا توجد موديولات إضافية مفعلة.</div>}</div>
        </section>
      </main>

      <aside className="space-y-5">
        <section className="rounded-[24px] border bg-slate-950 p-6 text-white shadow-sm">
          <div className="flex items-center gap-3"><CreditCard className="size-5 text-cyan-300" /><h2 className="font-black">الاشتراك</h2></div>
          <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 p-4"><div className="text-xs text-slate-400">الحالة</div><div className="mt-1 text-xl font-black">{settings?.is_trial ? "تجربة مجانية" : "اشتراك نشط"}</div>{settings?.trial_ends_at && <div className="mt-2 text-xs text-slate-400">تنتهي: {new Date(settings.trial_ends_at).toLocaleDateString("ar-EG")}</div>}</div>
          <div className="mt-4 space-y-2 text-sm text-slate-300"><div className="flex items-center gap-2"><Clock3 className="size-4" /> {settings?.status}</div><div className="flex items-center gap-2"><WalletCards className="size-4" /> {settings?.currency_code}</div></div>
          {user?.is_platform_admin && <Link to="/saas" className="mt-5 inline-flex items-center gap-2 text-sm font-bold text-cyan-300">إدارة الاشتراك <ChevronLeft className="size-4" /></Link>}
        </section>

        <section className="rounded-[24px] border bg-card p-6 shadow-sm"><h2 className="text-lg font-black">الوصول والأمان</h2><div className="mt-4 space-y-2"><SettingsLink icon={Users} title="المستخدمون والأدوار" to="/users" /><SettingsLink icon={ShieldCheck} title="الصلاحيات" to="/permissions" /><SettingsLink icon={KeyRound} title="الأدوار والوصول" to="/roles" /><SettingsLink icon={Bell} title="الدعم والمساعدة" to="/helpdesk" /></div></section>
        <section className="rounded-[24px] border bg-card p-6 shadow-sm"><h2 className="text-lg font-black">إدارة المؤسسة</h2><div className="mt-4 space-y-2"><SettingsLink icon={Building2} title="الشركات" to="/companies" /><SettingsLink icon={Building2} title="الفروع" to="/branches" /><SettingsLink icon={Languages} title="المستندات القانونية" to="/settings/legal" /><SettingsLink icon={LockKeyhole} title="الخصوصية" to="/privacy" /></div></section>
      </aside>
    </div>
  </div>;
}

function SettingsLink({ icon: Icon, title, to }: { icon: typeof Users; title: string; to: string }) {
  return <Link to={to} className="flex items-center justify-between rounded-xl border bg-slate-50 px-4 py-3 text-sm font-bold transition hover:border-blue-200 hover:bg-blue-50"><span className="flex items-center gap-3"><Icon className="size-4 text-blue-600" />{title}</span><ChevronLeft className="size-4 text-slate-400" /></Link>;
}
