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
  { icon: WalletCards, ar: "المالية والمحاسبة", en: "Finance & accounting", detailAr: "الحسابات والخزينة والميزانيات والأصول", detailEn: "Accounting, treasury, budgets and assets", tone: "text-cyan-300 bg-cyan-400/10" },
  { icon: Package, ar: "المبيعات والمشتريات", en: "Sales & purchasing", detailAr: "إدارة العملاء والموردين ودورة التجارة", detailEn: "Customers, suppliers and commercial workflows", tone: "text-sky-300 bg-sky-400/10" },
  { icon: Layers3, ar: "المخزون وسلاسل الإمداد", en: "Inventory & supply chain", detailAr: "المخازن والتصنيع والجودة والصيانة", detailEn: "Warehousing, manufacturing, quality and maintenance", tone: "text-amber-300 bg-amber-400/10" },
  { icon: Users2, ar: "الموارد البشرية والرواتب", en: "HR & payroll", detailAr: "الموظفون والحضور والانصراف والرواتب", detailEn: "Employees, attendance and payroll", tone: "text-teal-300 bg-teal-400/10" },
  { icon: BarChart3, ar: "التقارير والتحليلات", en: "Reports & analytics", detailAr: "مؤشرات الأداء والرؤية الإدارية", detailEn: "Performance indicators and management insight", tone: "text-blue-300 bg-blue-400/10" },
  { icon: Bot, ar: "الذكاء الاصطناعي", en: "AI assistant", detailAr: "مساعدة ذكية لفهم البيانات وسير العمل", detailEn: "Intelligent assistance for data and workflows", tone: "text-violet-300 bg-violet-400/10" },
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
    <main className="min-h-screen bg-[#edf2f7] p-0 text-slate-900" dir="ltr">
      <div className="grid min-h-screen w-full lg:grid-cols-[minmax(0,1.12fr)_minmax(420px,0.88fr)]">
        <section dir={isArabic ? "rtl" : "ltr"} className="relative flex min-h-[560px] flex-col overflow-hidden bg-[#07172b] px-6 py-7 text-white sm:px-10 sm:py-9 lg:min-h-screen lg:px-12 lg:py-10 xl:px-16">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_75%_25%,rgba(20,119,176,0.32),transparent_48%),linear-gradient(145deg,#0b2340_0%,#07172b_55%,#04101f_100%)]" />
          <div className="pointer-events-none absolute -bottom-36 -right-20 h-[28rem] w-[28rem] rounded-full border border-cyan-300/10" />
          <div className="pointer-events-none absolute -bottom-24 -right-8 h-[22rem] w-[22rem] rounded-full border border-cyan-300/[0.07]" />

          <header className="relative z-10 flex items-center gap-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-300 to-cyan-600 shadow-lg shadow-cyan-950/40">
              <span className="text-2xl font-black text-[#062038]">P</span>
            </div>
            <div>
              <div className="text-3xl font-black tracking-tight sm:text-4xl">Prime<span className="text-cyan-400">ERP</span></div>
              <div className="mt-1 text-[10px] font-semibold tracking-[0.2em] text-slate-400">BUSINESS OPERATING SYSTEM</div>
            </div>
          </header>

          <div className="relative z-10 my-auto max-w-3xl py-12 lg:py-14">
            <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-teal-300/20 bg-teal-300/10 px-4 py-2 text-xs font-semibold text-teal-200">
              <Layers3 className="h-4 w-4" />{text("منصة موحدة لإدارة المؤسسة", "INTEGRATED ENTERPRISE PLATFORM")}
            </div>
            <h1 className="max-w-2xl text-3xl font-black leading-[1.25] tracking-tight sm:text-4xl xl:text-5xl">{text("إدارة متكاملة لأعمالك. رؤية أوضح لقراراتك.", "One platform for your business. Clarity for every decision.")}</h1>
            <p className="mt-5 max-w-2xl text-sm leading-8 text-slate-300 sm:text-base">{text("PrimeERP يجمع الإدارة المالية والتجارية والتشغيلية والموارد البشرية والتقارير في نظام واحد، مع إدارة مركزية للشركات والفروع والصلاحيات.", "PrimeERP brings finance, commercial operations, supply chain, HR and reporting together, with centralized company, branch and access management.")}</p>

            <div className="mt-9 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {capabilities.map(({ icon: Icon, ar, en, detailAr, detailEn, tone }) => (
                <div key={en} className="flex min-h-[112px] items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.045] p-4 backdrop-blur-sm transition hover:border-cyan-300/25 hover:bg-white/[0.075]">
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${tone}`}><Icon className="h-5 w-5" /></div>
                  <div className="min-w-0"><h3 className="text-sm font-bold text-white">{text(ar, en)}</h3><p className="mt-1.5 text-[11px] leading-5 text-slate-400">{text(detailAr, detailEn)}</p></div>
                </div>
              ))}
            </div>

            <div className="mt-8 grid grid-cols-1 gap-3 rounded-2xl border border-cyan-300/15 bg-[#0b2945]/75 p-4 sm:grid-cols-3 sm:p-5">
              <div className="flex items-center gap-3"><Building2 className="h-6 w-6 shrink-0 text-cyan-300" /><div><p className="text-xs font-bold">{text("متعدد الشركات والفروع", "Multi-company")}</p><p className="mt-1 text-[10px] text-slate-400">{text("مساحات عمل مستقلة", "Independent workspaces")}</p></div></div>
              <div className="flex items-center gap-3"><ShieldCheck className="h-6 w-6 shrink-0 text-teal-300" /><div><p className="text-xs font-bold">{text("أمان وصلاحيات", "Secure by design")}</p><p className="mt-1 text-[10px] text-slate-400">{text("تحكم دقيق في الوصول", "Granular access control")}</p></div></div>
              <div className="flex items-center gap-3"><Workflow className="h-6 w-6 shrink-0 text-sky-300" /><div><p className="text-xs font-bold">{text("سير عمل مترابط", "Connected workflows")}</p><p className="mt-1 text-[10px] text-slate-400">{text("منظومة واحدة لأعمالك", "One connected system")}</p></div></div>
            </div>
          </div>

          <footer className="relative z-10 flex flex-wrap items-center justify-between gap-3 border-t border-white/10 pt-5 text-[10px] text-slate-500">
            <span>© {new Date().getFullYear()} PrimeERP. {text("جميع الحقوق محفوظة.", "All rights reserved.")}</span>
            <span>{text("إدارة أفضل • قرارات أدق • نمو مستدام", "Better management • Smarter decisions • Sustainable growth")}</span>
          </footer>
        </section>

        <section dir={isArabic ? "rtl" : "ltr"} className="relative flex min-h-screen items-center justify-center bg-gradient-to-br from-white via-[#fbfdff] to-[#f3f8fb] px-5 py-8 sm:px-10 lg:px-12 xl:px-16">
          <button type="button" onClick={changeLanguage} className="absolute end-6 top-6 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-teal-300 hover:text-teal-700">
            <Globe2 className="h-4 w-4 text-teal-700" />{isArabic ? "العربية" : "English"}
          </button>

          <div className="w-full max-w-[460px] py-12">
            <div className="mb-9 text-center">
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-600 shadow-lg shadow-teal-700/20"><span className="text-2xl font-black text-white">P</span></div>
              <div className="text-xl font-black tracking-tight text-slate-900">Prime<span className="text-teal-600">ERP</span></div>
              <p className="mt-1 text-[9px] font-semibold tracking-[0.2em] text-slate-400">BUSINESS OPERATING SYSTEM</p>
              <h2 className="mt-8 text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">{text("مرحبًا بك في PrimeERP", "Welcome to PrimeERP")}</h2>
              <p className="mt-2 text-sm text-slate-500">{text("يرجى تسجيل الدخول للمتابعة إلى مساحة العمل", "Sign in to continue to your workspace")}</p>
            </div>

            {error && <div role="alert" className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-6 text-red-700">{error}</div>}

            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="space-y-2">
                <Label htmlFor="companyName" className="text-sm font-semibold text-slate-700">{text("الشركة", "Company")}</Label>
                <div className="relative">
                  <Building2 className="pointer-events-none absolute start-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" />
                  <Input id="companyName" name="companyName" value={companyName} onChange={e => { setCompanyName(e.target.value); setError(""); }} placeholder={text("اسم الشركة (عند الحاجة)", "Company name (if required)")} autoComplete="organization" disabled={isLoading} className="h-[52px] rounded-xl border-slate-200 bg-white ps-11 shadow-sm placeholder:text-slate-400 focus-visible:border-teal-500 focus-visible:ring-teal-500/20" />
                </div>
                <p className="text-[11px] leading-5 text-slate-400">{text("أدخل اسم الشركة إذا كان حسابك مرتبطًا بأكثر من شركة.", "Enter the company name if your account matches more than one company.")}</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="login" className="text-sm font-semibold text-slate-700">{text("اسم المستخدم", "Username or email")}</Label>
                <div className="relative">
                  <Users2 className="pointer-events-none absolute start-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" />
                  <Input id="login" name="login" value={loginValue} onChange={e => { setLoginValue(e.target.value); setError(""); }} placeholder={text("أدخل اسم المستخدم أو البريد الإلكتروني", "Enter your username or email")} autoComplete="username" autoCapitalize="none" spellCheck={false} disabled={isLoading} required className="h-[52px] rounded-xl border-slate-200 bg-white ps-11 shadow-sm placeholder:text-slate-400 focus-visible:border-teal-500 focus-visible:ring-teal-500/20" dir="ltr" />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password" className="text-sm font-semibold text-slate-700">{text("كلمة المرور", "Password")}</Label>
                <div className="relative">
                  <LockKeyhole className="pointer-events-none absolute start-4 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-slate-400" />
                  <Input id="password" name="password" type={showPassword ? "text" : "password"} value={password} onChange={e => { setPassword(e.target.value); setError(""); }} placeholder={text("أدخل كلمة المرور", "Enter your password")} autoComplete="current-password" disabled={isLoading} required className="h-[52px] rounded-xl border-slate-200 bg-white ps-11 pe-12 shadow-sm placeholder:text-slate-400 focus-visible:border-teal-500 focus-visible:ring-teal-500/20" />
                  <button type="button" onClick={() => setShowPassword(v => !v)} disabled={isLoading} aria-label={showPassword ? text("إخفاء كلمة المرور", "Hide password") : text("إظهار كلمة المرور", "Show password")} className="absolute end-3 top-1/2 -translate-y-1/2 rounded-md p-2 text-slate-400 transition hover:text-teal-700">{showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
                </div>
              </div>

              <div className="flex items-center justify-between gap-3 pt-1">
                <label className="flex cursor-pointer items-center gap-2.5 text-sm text-slate-600"><input type="checkbox" checked={rememberMe} onChange={e => setRememberMe(e.target.checked)} disabled={isLoading} className="h-4 w-4 rounded border-slate-300 accent-teal-600" />{text("تذكرني", "Remember me")}</label>
                <span className="text-[11px] text-slate-400">{text("للمساعدة تواصل مع مسؤول النظام", "Contact your administrator for help")}</span>
              </div>

              <Button type="submit" disabled={isLoading} className="h-[52px] w-full rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 text-sm font-bold text-white shadow-lg shadow-teal-700/20 transition hover:from-teal-700 hover:to-cyan-700">
                {isLoading ? <><Loader2 className="h-4 w-4 animate-spin" />{text("جارٍ تسجيل الدخول...", "Signing in...")}</> : <>{text("تسجيل الدخول", "Sign in")}<ArrowRight className={isArabic ? "h-4 w-4 rotate-180" : "h-4 w-4"} /></>}
              </Button>
            </form>

            <div className="mt-8 flex items-center justify-center gap-2 text-xs text-slate-400"><ShieldCheck className="h-4 w-4 text-teal-600" />{text("دخول آمن إلى مساحة عملك", "Secure access to your workspace")}</div>
            <div className="mt-7 border-t border-slate-100 pt-6 text-center text-sm text-slate-500">{text("ليس لديك حساب؟", "Don't have an account?")}{" "}<Link to="/register" className="font-bold text-teal-700 transition hover:text-teal-900 hover:underline">{text("إنشاء حساب", "Create an account")}</Link></div>
          </div>
        </section>
      </div>
    </main>
  );
}
