import { useEffect, useState } from "react";
import { Bell, ChevronLeft, Command, Languages, LogOut, Menu, Moon, Settings2, ShieldCheck, Sun, UserCircle2 } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import client from "@/shared/api/client";
import { storage } from "@/shared/utils/storage";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/modules/identity/context/AuthContext";
import { findNavigationItemByPath, findNavigationParent } from "@/app/navigation";

interface AppHeaderProps { onMenuClick: () => void; }
const THEME_KEY = "primeerp_theme";
type CompanyOption = { id: number; name: string };
type BranchOption = { id: number; name: string };

export default function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { i18n, t } = useTranslation();
  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [branches, setBranches] = useState<BranchOption[]>([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState(() => storage.getCompanyId() || "");
  const [selectedBranchId, setSelectedBranchId] = useState(() => storage.getBranchId() || "");
  const [contextRevision, setContextRevision] = useState(0);
  const [dark, setDark] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(THEME_KEY) === "dark";
  });
  const language = i18n.resolvedLanguage?.startsWith("ar") ? "ar" : "en";
  const isArabic = language === "ar";

  useEffect(() => {
    const refreshContext = () => setContextRevision((value) => value + 1);
    window.addEventListener("primeerp:context-changed", refreshContext);
    return () => window.removeEventListener("primeerp:context-changed", refreshContext);
  }, []);

  useEffect(() => {
    if (!user) {
      setCompanies([]);
      setBranches([]);
      return;
    }
    if (!user.is_platform_admin && user.tenant_id) {
      storage.setTenantId(user.tenant_id);
    }
    if (user.is_platform_admin && !storage.getTenantId()) {
      setCompanies([]);
      setBranches([]);
      setSelectedCompanyId("");
      setSelectedBranchId("");
      return;
    }

    let cancelled = false;
    const loadContext = async () => {
      try {
        const response = await client.get<CompanyOption[]>("/companies?active_only=true");
        if (cancelled) return;
        const available = response.data;
        setCompanies(available);
        const savedCompanyId = storage.getCompanyId() || "";
        const savedCompany = available.find((company) => String(company.id) === savedCompanyId);
        const selectedCompany = savedCompany || (!user.is_platform_admin ? available[0] : undefined);

        if (!selectedCompany) {
          storage.clearCompanyContext();
          setSelectedCompanyId("");
          setSelectedBranchId("");
          setBranches([]);
          return;
        }

        storage.setCompanyId(selectedCompany.id);
        setSelectedCompanyId(String(selectedCompany.id));
        const branchResponse = await client.get<BranchOption[]>("/branches", {
          params: { company_id: selectedCompany.id, active_only: true },
        });
        if (cancelled) return;
        const availableBranches = branchResponse.data;
        setBranches(availableBranches);
        const savedBranchId = storage.getBranchId() || "";
        const savedBranch = availableBranches.find((branch) => String(branch.id) === savedBranchId);
        if (savedBranch) {
          setSelectedBranchId(String(savedBranch.id));
        } else {
          storage.clearBranchContext();
          setSelectedBranchId("");
        }
      } catch {
        if (!cancelled) {
          setCompanies([]);
          setBranches([]);
        }
      }
    };

    void loadContext();
    return () => {
      cancelled = true;
    };
  }, [user, contextRevision]);

  const changeCompanyContext = (value: string) => {
    storage.setCompanyId(value || null);
    storage.clearBranchContext();
    setSelectedCompanyId(value);
    setSelectedBranchId("");
    window.location.reload();
  };

  const changeBranchContext = (value: string) => {
    storage.setBranchId(value || null);
    setSelectedBranchId(value);
    window.location.reload();
  };

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem(THEME_KEY, dark ? "dark" : "light");
    document.documentElement.style.colorScheme = dark ? "dark" : "light";
  }, [dark]);

  const handleLogout = () => { logout(); navigate("/login", { replace: true }); };
  const currentItem = findNavigationItemByPath(location.pathname);
  const parentItem = findNavigationParent(location.pathname);
  const userName = user?.full_name || user?.username || user?.email || t("common.user", { defaultValue: isArabic ? "مستخدم" : "User" });
  const roleName = user?.is_platform_admin || user?.is_superuser ? t("common.platformAdministrator", { defaultValue: isArabic ? "مسؤول المنصة" : "Platform administrator" }) : user?.role_name || user?.role || t("common.systemUser", { defaultValue: isArabic ? "مستخدم النظام" : "System user" });

  return <header className="sticky top-0 z-30 border-b border-border/80 bg-background/90 text-foreground backdrop-blur-xl">
    <div className="flex h-[76px] items-center justify-between gap-3 px-4 sm:px-6 xl:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <Button type="button" variant="outline" size="icon" className="h-10 w-10 shrink-0 rounded-xl lg:hidden" onClick={onMenuClick} aria-label={isArabic ? "فتح القائمة" : "Open navigation"}><Menu className="h-5 w-5" /></Button>
        <div className="min-w-0">
          <div className="mb-1 hidden items-center gap-1.5 text-[11px] font-medium text-muted-foreground sm:flex"><Command className="h-3.5 w-3.5" /><span>PrimeERP</span>{parentItem && <><ChevronLeft className="h-3 w-3" /><span>{t(`navigation.${parentItem.id}`, { defaultValue: isArabic ? parentItem.labelAr : parentItem.label })}</span></>}{currentItem && <><ChevronLeft className="h-3 w-3" /><span className="text-foreground">{t(`navigation.${currentItem.id}`, { defaultValue: isArabic ? currentItem.labelAr : currentItem.label })}</span></>}</div>
          <h1 className="truncate text-base font-extrabold tracking-tight sm:text-lg">{currentItem ? t(`navigation.${currentItem.id}`, { defaultValue: isArabic ? currentItem.labelAr : currentItem.label }) : location.pathname === "/dashboard" ? t("navigation.dashboard", { defaultValue: isArabic ? "لوحة التحكم" : "Dashboard" }) : t("common.workspace", { defaultValue: isArabic ? "مساحة العمل" : "Workspace" })}</h1>
          <p className="mt-0.5 hidden max-w-[44vw] truncate text-xs text-muted-foreground md:block">{user?.tenant_name || t("common.integratedBusinessManagement", { defaultValue: isArabic ? "منصة إدارة الأعمال المتكاملة" : "Integrated business management" })} · {t("common.connectedBusinessOperations", { defaultValue: isArabic ? "متابعة مترابطة للأعمال والعمليات" : "Connected business operations" })}</p>
        </div>
      </div>
      <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
        {companies.length > 0 && <select
          value={selectedCompanyId}
          onChange={(event) => changeCompanyContext(event.target.value)}
          className="hidden max-w-40 rounded-xl border border-border bg-background px-2 py-2 text-xs font-semibold text-foreground md:inline-flex"
          aria-label={isArabic ? "الشركة النشطة" : "Active company"}
          title={isArabic ? "الشركة النشطة" : "Active company"}
        >
          {user?.is_platform_admin && <option value="">{isArabic ? "اختر الشركة" : "Select company"}</option>}
          {companies.map((company) => <option key={company.id} value={company.id}>{company.name}</option>)}
        </select>}
        {selectedCompanyId && branches.length > 0 && <select
          value={selectedBranchId}
          onChange={(event) => changeBranchContext(event.target.value)}
          className="hidden max-w-36 rounded-xl border border-border bg-background px-2 py-2 text-xs font-semibold text-foreground lg:inline-flex"
          aria-label={isArabic ? "نطاق الفرع" : "Branch scope"}
          title={isArabic ? "نطاق الفرع" : "Branch scope"}
        >
          <option value="">{isArabic ? "كل الشركة" : "Company-wide"}</option>
          {branches.map((branch) => <option key={branch.id} value={branch.id}>{branch.name}</option>)}
        </select>}
        <Button type="button" variant="outline" size="icon" className="h-9 w-9 rounded-xl" onClick={() => void i18n.changeLanguage(isArabic ? "en" : "ar")} aria-label={isArabic ? "Switch to English" : "التبديل إلى العربية"} title={isArabic ? "English" : "العربية"}><Languages className="h-4 w-4" /><span className="sr-only">{isArabic ? "English" : "العربية"}</span></Button>
        <Button type="button" variant="outline" size="icon" className="h-9 w-9 rounded-xl" onClick={() => setDark((value) => !value)} aria-label={dark ? (isArabic ? "الوضع الفاتح" : "Light mode") : (isArabic ? "الوضع الداكن" : "Dark mode")} title={dark ? (isArabic ? "الوضع الفاتح" : "Light mode") : (isArabic ? "الوضع الداكن" : "Dark mode")}>{dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}</Button>
        <Button type="button" variant="outline" size="icon" className="hidden h-9 w-9 rounded-xl sm:inline-flex" onClick={() => navigate("/settings/center")} aria-label={isArabic ? "الإعدادات" : "Settings"} title={isArabic ? "الإعدادات" : "Settings"}><Settings2 className="h-4 w-4" /></Button>
        <Button type="button" variant="outline" size="icon" className="relative h-9 w-9 rounded-xl" onClick={() => navigate("/notifications")} aria-label={isArabic ? "الرسائل والإشعارات" : "Notifications"} title={isArabic ? "الرسائل والإشعارات" : "Notifications"}><Bell className="h-4 w-4" /><span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-cyan-500 ring-2 ring-background" /></Button>
        <div className="hidden h-9 w-px bg-border sm:block" />
        <div className="hidden items-center gap-2.5 sm:flex"><div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-md shadow-blue-500/20">{user?.is_platform_admin || user?.is_superuser ? <ShieldCheck className="h-5 w-5" /> : <UserCircle2 className="h-5 w-5" />}</div><div className="max-w-36"><p className="truncate text-xs font-bold">{userName}</p><p className="mt-1 truncate text-[10px] text-muted-foreground">{roleName}</p></div></div>
        <Button type="button" variant="ghost" size="icon" className="h-9 w-9 rounded-xl text-muted-foreground hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/40" onClick={handleLogout} aria-label={isArabic ? "تسجيل الخروج" : "Sign out"} title={isArabic ? "تسجيل الخروج" : "Sign out"}><LogOut className="h-4 w-4" /></Button>
      </div>
    </div>
    <div className="h-[2px] bg-gradient-to-l from-blue-700 via-blue-500 to-cyan-400" />
  </header>;
}
