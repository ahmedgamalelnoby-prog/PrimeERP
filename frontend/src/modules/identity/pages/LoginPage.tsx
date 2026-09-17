import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import {
  ArrowRight, BarChart3, Bot, Building2, Eye, EyeOff, Globe2, Layers3,
  Loader2, LockKeyhole, Package, ReceiptText, ShieldCheck, Sparkles, Users2,
  WalletCards, Workflow
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/modules/identity/hooks/useAuth";

interface LoginLocationState { registrationSuccess?: boolean; username?: string; }

const valueProps = [
  { icon: BarChart3, ar: "لوحات تحكم وتحليلات لحظية", en: "Real-time dashboards & analytics", detailAr: "رؤية واضحة للإيرادات والمصروفات والمخزون والأداء.", detailEn: "See revenue, expenses, inventory and performance in one view." },
  { icon: WalletCards, ar: "محاسبة وخزينة متكاملة", en: "Accounting & treasury", detailAr: "حسابات عامة، فواتير، بنوك، خزائن وشيكات في دورة واحدة.", detailEn: "Accounting, invoices, banks, cash and checks in one connected flow." },
  { icon: Workflow, ar: "عمليات مترابطة من البداية للنهاية", en: "End-to-end workflows", detailAr: "المبيعات والمشتريات والمخزون والشحن والعمليات تعمل معًا.", detailEn: "Sales, purchasing, inventory, shipping and operations work together." },
  { icon: Bot, ar: "مساعد Prime AI", en: "Prime AI assistant", detailAr: "مساعدة ذكية للإجابة عن أسئلة النظام وتحليل الأعمال.", detailEn: "AI assistance for product questions and business analysis." },
  { icon: ShieldCheck, ar: "صلاحيات وأمان على مستوى المؤسسة", en: "Enterprise security", detailAr: "مستخدمون وأدوار وصلاحيات وسجل تدقيق وعزل بيانات العملاء.", detailEn: "Users, roles, permissions, audit trails and tenant isolation." },
  { icon: Layers3, ar: "نظام مرن متعدد الشركات والفروع", en: "Multi-company & multi-branch", detailAr: "إدارة أكثر من شركة وفرع من منصة SaaS واحدة.", detailEn: "Run multiple companies and branches from one SaaS platform." },
];

const moduleGroups = [
  { titleAr: "المالية", titleEn: "Finance", items: ["Accounting", "Treasury", "Invoicing", "Taxes", "Assets", "Budgets"] },
  { titleAr: "التجارة", titleEn: "Commercial", items: ["CRM", "Sales", "Purchasing", "Subscriptions", "Rental", "POS"] },
  { titleAr: "التشغيل", titleEn: "Operations", items: ["Inventory", "Shipping", "Manufacturing", "Quality", "Maintenance", "Restaurant"] },
  { titleAr: "المؤسسة", titleEn: "Enterprise", items: ["HR", "Payroll", "Projects", "Help Desk", "Documents", "Reports"] },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { i18n } = useTranslation();
  const { login } = useAuth();
  const locationState = location.state as LoginLocationState | null;
  const currentLanguage = i18n.resolvedLanguage ?? i18n.language;
  const isArabic = currentLanguage.toLowerCase().startsWith("ar");
  const [loginValue, setLoginValue] = useState(locationState?.username ?? "");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const text = (ar: string, en: string) => isArabic ? ar : en;

  useEffect(() => {
    const saved = localStorage.getItem("primeerp_remember_login");
    if (!locationState?.username && saved) { setLoginValue(saved); setRememberMe(true); }
  }, [locationState?.username]);

  useEffect(() => {
    if (locationState?.registrationSuccess) {
      toast.success(text("تم إنشاء الحساب بنجاح. يمكنك تسجيل الدخول الآن.", "Account created successfully. You can sign in now."));
      navigate("/login", { replace: true, state: null });
    }
  }, [locationState?.registrationSuccess, navigate]);

  const changeLanguage = async () => { await i18n.changeLanguage(isArabic ? "en" : "ar"); };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");
    const normalizedLogin = loginValue.trim();
    if (!normalizedLogin || !password) {
      setError(text("من فضلك أدخل اسم المستخدم وكلمة المرور.", "Please enter your username and password."));
      return;
    }
    try {
      setIsLoading(true);
      await login(normalizedLogin, password);
      if (rememberMe) localStorage.setItem("primeerp_remember_login", normalizedLogin);
      else localStorage.removeItem("primeerp_remember_login");
      toast.success(text("مرحبًا بك في PrimeERP", "Welcome back to PrimeERP"));
      navigate("/dashboard", { replace: true });
    } catch (loginError: unknown) {
      if (axios.isAxiosError(loginError)) {
        if (!loginError.response) setError(text("تعذر الاتصال بالخادم.", "Unable to connect to the server."));
        else if ([400, 401].includes(loginError.response.status)) setError(text("بيانات الدخول غير صحيحة.", "Invalid login credentials."));
        else if (loginError.response.status === 403) setError(String(loginError.response.data?.detail ?? text("الحساب غير نشط.", "Account is inactive.")));
        else if (loginError.response.status === 422) setError(text("الطلب غير صالح.", "Invalid request."));
        else setError(text("حدث خطأ غير متوقع.", "Something went wrong."));
      } else setError(text("حدث خطأ غير متوقع.", "Something went wrong."));
    } finally { setIsLoading(false); }
  };

  return (
    <main className="min-h-screen bg-[#f7f9fc] text-slate-950" dir={isArabic ? "rtl" : "ltr"}>
      <div className="grid min-h-screen lg:grid-cols-[1.15fr_0.85fr]">
        <section className="relative hidden overflow-hidden bg-slate-950 px-10 py-10 text-white lg:flex lg:flex-col">
          <div className="absolute -left-32 -top-32 size-96 rounded-full bg-blue-600/20 blur-3xl" />
          <div className="absolute -right-24 bottom-0 size-96 rounded-full bg-cyan-500/10 blur-3xl" />
          <div className="relative z-10 flex items-center justify-between">
            <Link to="/" className="flex items-center gap-3">
              <div className="flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-blue-950/50"><Building2 className="size-6" /></div>
              <div><div className="text-xl font-extrabold">Prime<span className="text-cyan-400">ERP</span></div><div className="text-xs text-slate-400">{text("منصة إدارة أعمال متكاملة", "Complete business management platform")}</div></div>
            </Link>
            <button type="button" onClick={changeLanguage} className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-slate-200 hover:bg-white/10"><Globe2 className="size-4" />{isArabic ? "English" : "العربية"}</button>
          </div>
          <div className="relative z-10 my-auto max-w-3xl py-16">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-4 py-2 text-sm font-semibold text-cyan-300"><Sparkles className="size-4" /> {text("الإصدار المتطور من PrimeERP", "The next generation of PrimeERP")}</div>
            <h1 className="max-w-3xl text-5xl font-black leading-[1.08] tracking-tight xl:text-6xl">{text("كل أعمالك. نظام واحد. رؤية أذكى.", "Your entire business. One platform. Smarter visibility.")}</h1>
            <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-300">{text("PrimeERP يربط الإدارة المالية والتجارية والتشغيلية والموارد البشرية في منصة SaaS واحدة، مع مساعد ذكاء اصطناعي يساعدك على فهم النظام واتخاذ قرارات أسرع.", "PrimeERP connects finance, commercial operations, supply chain and HR in one SaaS platform, with AI assistance that helps teams understand the system and move faster.")}</p>
            <div className="mt-10 grid gap-4 sm:grid-cols-2">
              {valueProps.map(({ icon: Icon, ar, en, detailAr, detailEn }) => (
                <div key={en} className="rounded-2xl border border-white/10 bg-white/[0.045] p-4 backdrop-blur transition hover:bg-white/[0.08]">
                  <div className="flex items-start gap-3"><div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-blue-500/15 text-cyan-300"><Icon className="size-5" /></div><div><div className="font-bold">{text(ar, en)}</div><p className="mt-1 text-xs leading-5 text-slate-400">{text(detailAr, detailEn)}</p></div></div>
                </div>
              ))}
            </div>
            <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
              {[[text("مالية", "Finance"), ReceiptText], [text("مبيعات", "Sales"), Package], [text("موارد بشرية", "HR"), Users2], [text("ذكاء اصطناعي", "AI"), Bot]].map(([label, Icon]) => <div key={String(label)} className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-3 text-center text-xs text-slate-300"><Icon className="mx-auto mb-2 size-4 text-cyan-300" /><span>{String(label)}</span></div>)}
            </div>
          </div>
          <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-5 text-xs text-slate-500"><span>© {new Date().getFullYear()} PrimeERP</span><span>{text("منصة أعمال سحابية متعددة الشركات", "Multi-company cloud ERP")}</span></div>
        </section>

        <section className="flex min-h-screen items-center justify-center px-5 py-8 sm:px-8 lg:px-12">
          <div className="w-full max-w-[520px]">
            <div className="mb-6 flex items-center justify-between lg:justify-end">
              <Link to="/" className="flex items-center gap-2 lg:hidden"><div className="flex size-10 items-center justify-center rounded-xl bg-blue-600 text-white"><Building2 className="size-5" /></div><span className="text-xl font-black">Prime<span className="text-blue-600">ERP</span></span></Link>
              <button type="button" onClick={changeLanguage} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 shadow-sm hover:bg-slate-50"><Globe2 className="size-4 text-blue-600" />{isArabic ? "English" : "العربية"}</button>
            </div>
            <div className="rounded-[28px] border border-slate-200 bg-white p-6 shadow-[0_24px_80px_rgba(15,23,42,0.10)] sm:p-9">
              <div className="mb-8"><div className="mb-4 flex size-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-600"><LockKeyhole className="size-6" /></div><div className="text-sm font-bold text-blue-600">{text("مرحبًا بك مجددًا", "Welcome back")}</div><h2 className="mt-2 text-3xl font-black tracking-tight">{text("تسجيل الدخول إلى PrimeERP", "Sign in to PrimeERP")}</h2><p className="mt-3 text-sm leading-6 text-slate-500">{text("ادخل إلى مساحة عملك لإدارة شركتك ومتابعة أعمالك من مكان واحد.", "Access your workspace to manage your company and keep operations connected.")}</p></div>
              {error && <div role="alert" className="mb-6 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">{error}</div>}
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-2"><Label htmlFor="login">{text("اسم المستخدم أو البريد الإلكتروني", "Username or email")}</Label><Input id="login" name="login" value={loginValue} onChange={e => { setLoginValue(e.target.value); setError(""); }} placeholder={text("أدخل اسم المستخدم أو البريد", "Enter username or email")} autoComplete="username" autoCapitalize="none" spellCheck={false} disabled={isLoading} required className="h-12 rounded-xl" dir="ltr" /></div>
                <div className="space-y-2"><div className="flex items-center justify-between gap-4"><Label htmlFor="password">{text("كلمة المرور", "Password")}</Label><Link to="/forgot-password" className="text-sm font-semibold text-blue-600 hover:underline">{text("نسيت كلمة المرور؟", "Forgot password?")}</Link></div><div className="relative"><Input id="password" name="password" type={showPassword ? "text" : "password"} value={password} onChange={e => { setPassword(e.target.value); setError(""); }} placeholder={text("أدخل كلمة المرور", "Enter your password")} autoComplete="current-password" disabled={isLoading} required className="h-12 rounded-xl pe-11" /><button type="button" onClick={() => setShowPassword(v => !v)} disabled={isLoading} aria-label={showPassword ? text("إخفاء كلمة المرور", "Hide password") : text("إظهار كلمة المرور", "Show password")} className="absolute end-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700">{showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div></div>
                <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-600"><input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} disabled={isLoading} className="size-4 rounded accent-blue-600" />{text("تذكر بيانات الدخول", "Remember me")}</label>
                <Button type="submit" disabled={isLoading} className="h-12 w-full rounded-xl bg-gradient-to-r from-blue-600 to-cyan-500 text-base font-bold shadow-lg shadow-blue-500/20 hover:from-blue-700 hover:to-cyan-600">{isLoading ? <><Loader2 className="size-4 animate-spin" />{text("جاري تسجيل الدخول...", "Signing in...")}</> : <>{text("دخول إلى مساحة العمل", "Enter workspace")}<ArrowRight className={isArabic ? "size-4 rotate-180" : "size-4"} /></>}</Button>
              </form>
              <div className="my-7 flex items-center gap-4"><div className="h-px flex-1 bg-slate-200" /><span className="text-xs font-semibold text-slate-400">{text("ابدأ مع PrimeERP", "START WITH PRIMEERP")}</span><div className="h-px flex-1 bg-slate-200" /></div>
              <div className="grid grid-cols-2 gap-3"><div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center"><ShieldCheck className="mx-auto size-5 text-blue-600" /><p className="mt-1 text-xs font-semibold">{text("أمان مؤسسي", "Enterprise security")}</p></div><div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-center"><Bot className="mx-auto size-5 text-cyan-600" /><p className="mt-1 text-xs font-semibold">{text("مساعدة بالـAI", "AI assistance")}</p></div></div>
              <p className="mt-7 text-center text-sm text-slate-600">{text("ليس لديك حساب؟", "Don't have an account?")}{" "}<Link to="/register" className="font-bold text-blue-600 hover:underline">{text("ابدأ التجربة المجانية", "Start free trial")}</Link></p>
            </div>
            <div className="mt-6"><p className="mb-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-400">{text("أهم ما تقدمه PrimeERP", "What PrimeERP brings together")}</p><div className="grid grid-cols-2 gap-2 sm:grid-cols-4">{moduleGroups.map(group => <div key={group.titleEn} className="rounded-xl border border-slate-200 bg-white px-3 py-3 text-center"><p className="text-xs font-bold text-slate-700">{text(group.titleAr, group.titleEn)}</p><p className="mt-1 text-[10px] leading-4 text-slate-400">{group.items.slice(0, 3).join(" • ")} +</p></div>)}</div></div>
          </div>
        </section>
      </div>
    </main>
  );
}
