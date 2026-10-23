import { Bell, ChevronLeft, Command, LogOut, Menu, Search, Settings2, ShieldCheck, UserCircle2 } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/modules/identity/context/AuthContext";
import { findNavigationItemByPath, findNavigationParent } from "@/app/navigation";

interface AppHeaderProps { onMenuClick: () => void; }

export default function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
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
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/90 backdrop-blur-xl">
      <div className="flex h-[76px] items-center justify-between gap-3 px-4 sm:px-6 xl:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Button type="button" variant="outline" size="icon" className="h-10 w-10 shrink-0 rounded-xl border-slate-200 bg-white lg:hidden" onClick={onMenuClick} aria-label="فتح القائمة">
            <Menu className="h-5 w-5" />
          </Button>
          <div className="min-w-0">
            <div className="mb-1 hidden items-center gap-1.5 text-[11px] font-medium text-slate-400 sm:flex">
              <Command className="h-3.5 w-3.5" />
              <span>PrimeERP</span>
              {parentItem && <><ChevronLeft className="h-3 w-3" /><span>{parentItem.labelAr}</span></>}
              {currentItem && <><ChevronLeft className="h-3 w-3" /><span className="text-slate-600">{currentItem.labelAr}</span></>}
            </div>
            <h1 className="truncate text-base font-extrabold tracking-tight text-slate-900 sm:text-lg">
              {currentItem?.labelAr || (location.pathname === "/dashboard" ? "لوحة التحكم" : "مساحة العمل")}
            </h1>
            <p className="mt-0.5 hidden max-w-[44vw] truncate text-xs text-slate-500 md:block">
              {user?.tenant_name || "منصة إدارة الأعمال المتكاملة"} · متابعة مترابطة للأعمال والعمليات
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <Button type="button" variant="outline" size="icon" className="hidden h-10 w-10 rounded-xl border-slate-200 text-slate-600 hover:bg-blue-50 hover:text-blue-700 sm:inline-flex" onClick={() => navigate("/settings")} aria-label="الإعدادات" title="الإعدادات">
            <Settings2 className="h-4 w-4" />
          </Button>
          <Button type="button" variant="outline" size="icon" className="relative h-10 w-10 rounded-xl border-slate-200 text-slate-600 hover:bg-blue-50 hover:text-blue-700" onClick={() => navigate("/notifications")} aria-label="الرسائل والإشعارات" title="الرسائل والإشعارات">
            <Bell className="h-4 w-4" />
            <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-cyan-500 ring-2 ring-white" />
          </Button>
          <div className="hidden h-9 w-px bg-slate-200 sm:block" />
          <div className="hidden items-center gap-2.5 sm:flex">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 text-white shadow-md shadow-blue-500/20">
              {user?.is_platform_admin || user?.is_superuser ? <ShieldCheck className="h-5 w-5" /> : <UserCircle2 className="h-5 w-5" />}
            </div>
            <div className="max-w-36">
              <p className="truncate text-xs font-bold text-slate-800">{userName}</p>
              <p className="mt-1 truncate text-[10px] text-slate-500">{roleName}</p>
            </div>
          </div>
          <Button type="button" variant="ghost" size="icon" className="h-10 w-10 rounded-xl text-slate-500 hover:bg-rose-50 hover:text-rose-600" onClick={handleLogout} aria-label="تسجيل الخروج" title="تسجيل الخروج">
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
      <div className="h-[2px] bg-gradient-to-l from-blue-700 via-blue-500 to-cyan-400" />
    </header>
  );
}
