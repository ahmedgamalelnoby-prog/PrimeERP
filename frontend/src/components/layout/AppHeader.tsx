import { Bell, LogOut, Menu, Search, UserCircle2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/modules/identity/context/AuthContext";

interface AppHeaderProps { onMenuClick: () => void; }

export default function AppHeader({ onMenuClick }: AppHeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const userName = user?.full_name || user?.username || user?.email || "مستخدم";
  const role = user?.is_platform_admin || user?.is_superuser ? "Super Admin" : "مستخدم النظام";
  const handleLogout = () => { logout(); navigate("/login", { replace: true }); };

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/85 backdrop-blur-xl">
      <div className="flex h-[72px] items-center justify-between gap-4 px-4 sm:px-6 xl:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <Button type="button" variant="outline" size="icon" className="rounded-xl lg:hidden" onClick={onMenuClick} aria-label="فتح القائمة"><Menu className="h-5 w-5" /></Button>
          <div className="hidden h-10 w-px bg-slate-200 sm:block" />
          <div className="min-w-0"><p className="truncate text-xs font-black uppercase tracking-[0.16em] text-blue-600">PrimeERP</p><h2 className="truncate text-base font-bold text-slate-900 sm:text-lg">نظام إدارة موارد المؤسسة</h2></div>
        </div>
        <div className="flex items-center gap-2 sm:gap-3">
          <div className="hidden items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500 xl:flex"><Search className="h-4 w-4" /> بحث سريع</div>
          <button type="button" className="relative flex size-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-500 hover:bg-slate-50" aria-label="الإشعارات"><Bell className="size-5" /><span className="absolute right-2 top-2 size-1.5 rounded-full bg-blue-600" /></button>
          <div className="hidden items-center gap-2 sm:flex"><div className="text-left"><p className="text-sm font-bold text-slate-800">{userName}</p><p className="text-xs text-slate-500">{role}</p></div><UserCircle2 className="size-9 text-slate-400" /></div>
          <Button type="button" variant="outline" size="sm" className="rounded-xl" onClick={handleLogout}><LogOut className="ml-2 h-4 w-4" /> خروج</Button>
        </div>
      </div>
    </header>
  );
}
