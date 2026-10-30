import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import toast from "react-hot-toast";
import { useTranslation } from "react-i18next";
import {
  ArrowRight, BarChart3, Bot, Building2, Eye, EyeOff, Globe2, Layers3,
  Loader2, LockKeyhole, Package, ShieldCheck, Users2, WalletCards, Workflow,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/modules/identity/hooks/useAuth";

interface LoginLocationState { registrationSuccess?: boolean; username?: string; }

const capabilities = [
  { icon: WalletCards, ar: "الإدارة المالية", en: "Finance", detailAr: "الحسابات والخزينة والميزانيات والأصول", detailEn: "Accounting, treasury, budgets and assets" },
  { icon: Package, ar: "الإدارة التجارية", en: "Commercial", detailAr: "المبيعات والمشتريات والعملاء ونقاط البيع", detailEn: "Sales, purchasing, CRM and point of sale" },
  { icon: Workflow, ar: "التشغيل وسلاسل الإمداد", en: "Operations & supply chain", detailAr: "المخزون والتصنيع والجودة والصيانة", detailEn: "Inventory, manufacturing, quality and maintenance" },
  { icon: Users2, ar: "الموارد البشرية", en: "Human resources", detailAr: "الموظفون والحضور والانصراف والرواتب", detailEn: "Employees, attendance and payroll" },
  { icon: BarChart3, ar: "التقارير والتحليلات", en: "Reports & analytics", detailAr: "مؤشرات الأداء وتقارير الإدارة", detailEn: "Management reports and performance insights" },
  { icon: Bot, ar: "الذكاء الاصطناعي", en: "Artificial intelligence", detailAr: "مساعد ذكي لدعم فهم البيانات والعمل", detailEn: "An intelligent assistant for business insights" },
];

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { i18n } = useTranslation();
  const { login } = useAuth();
  const locationState = location.state as LoginLocationState | null;
  const currentLanguage = i18n.resolvedLanguage ?? i18n.language;
  const isArabic = currentLanguage.toLowerCase().startsWith("ar");
  const [companyName, setCompanyName] = useState("");
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
      await login(normalizedLogin, password, null, companyName.trim() || null);
      if (rememberMe) localStorage.setItem("primeerp_remember_login", normalizedLogin);
      else localStorage.removeItem("primeerp_remember_login");
      toast.success(text("مرحبًا بك في PrimeERP", "Welcome back to PrimeERP"));
      navigate("/dashboard", { replace: true });
    } catch (loginError: unknown) {
      if (axios.isAxiosError(loginError)) {
        const status = loginError.response?.status;
        const detail = loginError.response?.data?.detail;
        if (!loginError.response) setError(text("تعذر الاتصال بالخادم.", "Unable to connect to the server."));
        else if ([400, 401].includes(status ?? 0)) setError(text("بيانات الدخول غير صحيحة.", "Invalid login credentials."));
        else if (status === 403) setError(String(detail ?? text("الحساب غير نشط.", "Account is inactive.")));
        else if (status === 409) setError(String(detail ?? text("يوجد تعارض في بيانات الدخول. راجع اسم الشركة.", "Login conflict. Please check the company name.")));
        else if (status === 422) setError(text("البيانات المدخلة غير مكتملة أو غير صالحة.", "The submitted information is incomplete or invalid."));
        else setError(String(detail ?? text("حدث خطأ غير متوقع.", "Something went wrong.")));
      } else setError(text("حدث خطأ غير متوقع.", "Something went wrong."));
    } finally { setIsLoading(false); }
  };

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#eef3f8] px-4 py-6 text-slate-900 sm:px-6 lg:px-8" dir={isArabic ? "rtl" : "ltr"}>
      <div className="pointer-events-none absolute -left-32 -top-32 h-96 w-96 rounded-full bg-cyan-200/40 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-40 -right-24 h-[30rem] w-[30rem] rounded-full bg-blue-200/40 blur-3xl" />

      <div className="relative grid w-full max-w-[1180px] overflow-hidden rounded-[28px] border border-white/80 bg-white shadow-[0_30px_100px_rgba(15,35,65,0.14)] lg:min-h-[720px] lg:grid-cols-[1.04fr_0.96fr]">
        <section className="relative flex flex-col overflow-hidden bg-[#102b43] px-6 py-7 text-white sm:px-9 sm:py-9 lg:px-11 lg:py-10">
          <div className="pointer-events-none absolute -right-28 -top-28 h-80 w-80 rounded-full border-[48px] border-cyan-300/[0.06]" />
          <div className="pointer-events-none absolute -bottom-40 -left-24 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl" />
          <div className="relative flex items-center justify-between gap-4">
            <Link to="/" className="flex items-center gap-3">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-white/15 bg-white/10 shadow-lg"><Building2 className="h-6 w-6 text-cyan-300" /></div>
              <div><div className="text-2xl font-black tracking-tight">Prime<span className="text-cyan-300">ERP</span></div><div className="mt-0.5 text-[10px] font-semibold tracking-[0.19em] text-slate-400">BUSINESS OPERATING SYSTEM</div></div>
            </Link>
            <button type="button" onClick={changeLanguage} className="inline-flex shrink-0 items-center gap-2 rounded-xl border border-white/15 bg-white/[0.06] px-3 py-2 text-xs font-semibold text-slate-200 transition hover:bg-white/10"><Globe2 className="h-4 w-4" />{isArabic ? "English" : "العربية"}</button>
          </div>

          <div className="relative my-8 lg:my-auto">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1.5 text-xs font-semibold text-cyan-200"><Layers3 className="h-3.5 w-3.5" />{text("منصة موحدة لإدارة المؤسسة", "One connected enterprise platform")}</div>
            <h1 className="max-w-xl text-3xl font-black leading-tight tracking-tight sm:text-4xl">{text("كل أقسام شركتك تعمل بتناغم.", "Every part of your business, working together.")}</h1>
            <p className="mt-4 max-w-xl text-sm leading-7 text-slate-300 sm:text-base">{text("منظومة متكاملة تربط الإدارة المالية والتجارية والتشغيلية والموارد البشرية في مساحة عمل واحدة، مع صلاحيات واضحة ورؤية موحدة للأعمال.", "A connected platform for finance, commercial operations, supply chain and people management, with clear access controls and a unified view of the business.")}</p>

            <div className="mt-8 grid gap-3 sm:grid-cols-2">
              {capabilities.map(({ icon: Icon, ar, en, detailAr, detailEn }) => (
                <div key={en} className="flex min-h-[82px] items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.055] p-3.5 transition hover:bg-white/[0.09]">
                  <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-cyan-300/10 text-cyan-200"><Icon className="h-[18px] w-[18px]" /></div>
                  <div className="min-w-0"><p className="text-sm font-bold text-white">{text(ar, en)}</p><p className="mt-1 text-[11px] leading-5 text-slate-400">{text(detailAr, detailEn)}</p></div>
                </div>
              ))}
            </div>

            <div className="mt-7 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-slate-400">
              <span className="inline-flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-emerald-300" />{text("صلاحيات وأمان مؤسسي", "Enterprise access & security")}</span>
              <span className="inline-flex items-center gap-2"><Workflow className="h-4 w-4 text-cyan-300" />{text("سير عمل مترابط", "Connected workflows")}</span>
            </div>
          </div>

          <div className="relative flex items-center justify-between border-t border-white/10 pt-4 text-[10px] text-slate-500"><span>© {new Date().getFullYear()} PrimeERP</span><span>{text("منصة إدارة موارد المؤسسة", "Enterprise resource planning")}</span></div>
        </section>

        <section className="flex items-center justify-center bg-white px-5 py-8 sm:px-9 lg:px-12">
          <div className="w-full max-w-[430px]">
            <div className="mb-8">
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-50 text-blue-700"><LockKeyhole className="h-6 w-6" /></div>
              <p className="text-sm font-bold text-blue-700">{text("مرحبًا بك مجددًا", "Welcome back")}</p>
              <h2 className="mt-2 text-3xl font-black tracking-tight text-slate-900">{text("تسجيل الدخول", "Sign in")}</h2>
              <p className="mt-3 text-sm leading-6 text-slate-500">{text("سجّل الدخول للوصول إلى مساحة العمل الخاصة بك.", "Sign in to access your workspace.")}</p>
            </div>

            {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">{error}</div>}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="companyName" className="text-sm font-semibold text-slate-700">{text("الشركة", "Company")}</Label>
                <Input id="companyName" name="companyName" value={companyName} onChange={e => { setCompanyName(e.target.value); setError(""); }} placeholder={text("اسم الشركة (عند الحاجة)", "Company name (if required)")} autoComplete="organization" disabled={isLoading} className="h-12 rounded-xl border-slate-200 bg-slate-50/60 focus-visible:bg-white" />
                <p className="text-[11px] leading-5 text-slate-400">{text("إذا كان حسابك مرتبطًا بأكثر من شركة، أدخل اسم الشركة المسجل.", "If your account is associated with multiple companies, enter the registered company name.")}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="login" className="text-sm font-semibold text-slate-700">{text("اسم المستخدم أو البريد الإلكتروني", "Username or email")}</Label>
                <Input id="login" name="login" value={loginValue} onChange={e => { setLoginValue(e.target.value); setError(""); }} placeholder={text("أدخل اسم المستخدم أو البريد", "Enter username or email")} autoComplete="username" autoCapitalize="none" spellCheck={false} disabled={isLoading} required className="h-12 rounded-xl border-slate-200 bg-slate-50/60 focus-visible:bg-white" dir="ltr" />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between gap-3"><Label htmlFor="password" className="text-sm font-semibold text-slate-700">{text("كلمة المرور", "Password")}</Label><span className="text-[11px] text-slate-400">{text("للمساعدة، تواصل مع مسؤول النظام", "Contact your administrator for help")}</span></div>
                <div className="relative">
                  <Input id="password" name="password" type={showPassword ? "text" : "password"} value={password} onChange={e => { setPassword(e.target.value); setError(""); }} placeholder={text("أدخل كلمة المرور", "Enter your password")} autoComplete="current-password" disabled={isLoading} required className="h-12 rounded-xl border-slate-200 bg-slate-50/60 pe-11 focus-visible:bg-white" />
                  <button type="button" onClick={() => setShowPassword(v => !v)} disabled={isLoading} aria-label={showPassword ? text("إخفاء كلمة المرور", "Hide password") : text("إظهار كلمة المرور", "Show password")} className="absolute end-3 top-1/2 -translate-y-1/2 rounded-md p-1 text-slate-400 hover:text-slate-700">{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
                </div>
              </div>

              <label className="flex cursor-pointer items-center gap-2.5 pt-1 text-sm text-slate-600"><input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} disabled={isLoading} className="h-4 w-4 rounded accent-blue-700" />{text("تذكر اسم المستخدم", "Remember username")}</label>

              <Button type="submit" disabled={isLoading} className="mt-2 h-12 w-full rounded-xl bg-[#1257a6] text-sm font-bold shadow-lg shadow-blue-900/15 transition hover:bg-[#0d478c]">
                {isLoading ? <><Loader2 className="h-4 w-4 animate-spin" />{text("جارٍ تسجيل الدخول...", "Signing in...")}</> : <>{text("دخول إلى النظام", "Sign in to PrimeERP")}<ArrowRight className={isArabic ? "h-4 w-4 rotate-180" : "h-4 w-4"} /></>}
              </Button>
            </form>

            <div className="mt-7 flex items-center justify-center gap-2 text-xs text-slate-400"><ShieldCheck className="h-4 w-4 text-emerald-600" />{text("اتصال آمن ومساحة عمل مخصصة", "Secure access to your workspace")}</div>
            <div className="mt-6 border-t border-slate-100 pt-5 text-center text-sm text-slate-500">{text("ليس لديك حساب؟", "Don't have an account?")}{" "}<Link to="/register" className="font-bold text-blue-700 hover:text-blue-900 hover:underline">{text("إنشاء حساب", "Create an account")}</Link></div>
          </div>
        </section>
      </div>
    </main>
  );
}
