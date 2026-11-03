import { Bell, Building2, ChevronLeft, Command, LogOut, Menu, Settings2, ShieldCheck, UserCircle2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/modules/identity/context/AuthContext";
import client from "@/shared/api/client";
import { findNavigationItemByPath, findNavigationParent } from "@/app/navigation";

interface AppHeaderProps { onMenuClick: () => void; }
interface CompanyOption { id: number; name: string; code?: string | null; is_default?: boolean; }

export default function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const [companies, setCompanies] = useState<CompanyOption[]>([]);
  const [companyId, setCompanyId] = useState(() => localStorage.getItem("company_id") || "");
  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    void client.get<CompanyOption[]>("/companies?active_only=true").then(({ data }) => {
      if (cancelled) return;
      setCompanies(data);
      const stored = Number(localStorage.getItem("company_id")) || 0;
      const selected = data.find((company) => company.id === stored)
        ?? data.find((company) => company.is_default)
        ?? data[0];
      if (selected) {
        setCompanyId(String(selected.id));
        localStorage.setItem("company_id", String(selected.id));
      } else {
        setCompanyId("");
        localStorage.removeItem("company_id");
      }
    }).catch(() => {
      if (!cancelled) setCompanies([]);
    });
    return () => { cancelled = true; };
  }, [user]);
  const handleCompanyChange = (nextId: string) => {
    if (!companies.some((company) => String(company.id) === nextId)) return;
    localStorage.setItem("company_id", nextId);
    setCompanyId(nextId);
    window.location.reload();
  };
  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const currentItem = findNavigationItemByPath(location.pathname);
  const parentItem = findNavigationParent(location.pathname);
  const userName = user?.full_name || user?.username || user?.email || "مستخدم";
  const roleName = user?.is_platform_admin || user?.is_superuser
    ? "مسؤول المنصة"
    : user?.role_name || user?.role || "مستخدم النظام";

  return (
    <header className="sticky top-0 z-30 border-b border-border/80 bg-card/90 backdrop-blur-xl">
      <div className="flex h-[76px] items-center justify-between gap-3 px-4 sm:px-6 xl:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Button type="button" variant="outline" size="icon" className="h-10 w-10 shrink-0 rounded-xl border-border bg-card lg:hidden" onClick={onMenuClick} aria-label="فتح القائمة">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0">
            <div className="mb-1 hidden items-center gap-1.5 text-[11px] font-medium text-muted-foreground sm:flex">
              <Command className="h-3.5 w-3.5" />
              <span>PrimeERP</span>
              {parentItem && <><ChevronLeft className="h-3 w-3 rtl:rotate-180" /><span>{parentItem.labelAr}</span></>}
              {currentItem && <><ChevronLeft className="h-3 w-3 rtl:rotate-180" /><span className="text-foreground/80">{currentItem.labelAr}</span></>}
            </div>
            <h1 className="truncate text-base font-extrabold tracking-tight text-foreground sm:text-lg">
              {currentItem?.labelAr || (location.pathname === "/dashboard" ? "لوحة التحكم" : "مساحة العمل")}
            </h1>
            <p className="mt-0.5 hidden max-w-[44vw] truncate text-xs text-muted-foreground md:block">
              {user?.tenant_name || "منصة إدارة الأعمال المتكاملة"} · متابعة مترابطة للأعمال والعمليات
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {companies.length > 1 && (
            <label className="hidden items-center gap-2 rounded-xl border border-border bg-background px-2.5 py-2 text-xs font-semibold text-foreground md:flex">
              <Building2 className="h-4 w-4 text-primary" />
              <span className="sr-only">الشركة الحالية</span>
              <select
                aria-label="الشركة الحالية"
                value={companyId}
                onChange={(event) => handleCompanyChange(event.target.value)}
                className="max-w-40 bg-transparent outline-none"
              >
                {companies.map((company) => (
                  <option key={company.id} value={String(company.id)}>
                    {company.name}{company.code ? " · " + company.code : ""}
                  </option>
                ))}
              </select>
            </label>
          )}
          <Button type="button" variant="outline" size="icon" className="hidden h-10 w-10 rounded-xl border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground sm:inline-flex" onClick={() => navigate("/settings")} aria-label="الإعدادات" title="الإعدادات">
            <Settings2 className="h-4 w-4" />
          </Button>
          <Button type="button" variant="outline" size="icon" className="relative h-10 w-10 rounded-xl border-border text-muted-foreground hover:bg-accent hover:text-accent-foreground" onClick={() => navigate("/notifications")} aria-label="الرسائل والإشعارات" title="الرسائل والإشعارات">
            <Bell className="h-4 w-4" />
            <span className="absolute end-2 top-2 h-1.5 w-1.5 rounded-full bg-primary ring-2 ring-card" />
          </Button>
          <div className="hidden h-9 w-px bg-border sm:block" />
          <div className="hidden items-center gap-2.5 sm:flex">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/70 text-primary-foreground shadow-md">
              {user?.is_platform_admin || user?.is_superuser ? <ShieldCheck className="h-5 w-5" /> : <UserCircle2 className="h-5 w-5" />}
            </div>
            <div className="max-w-36">
              <p className="truncate text-xs font-bold text-foreground">{userName}</p>
              <p className="mt-1 truncate text-[10px] text-muted-foreground">{roleName}</p>
            </div>
          </div>
          <Button type="button" variant="ghost" size="icon" className="h-10 w-10 rounded-xl text-muted-foreground hover:bg-destructive/10 hover:text-destructive" onClick={handleLogout} aria-label="تسجيل الخروج" title="تسجيل الخروج">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="h-[2px] bg-gradient-to-l rtl:bg-gradient-to-r from-primary via-primary/70 to-accent" />
    </header>
  );
}