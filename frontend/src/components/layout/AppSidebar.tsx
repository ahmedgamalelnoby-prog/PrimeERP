import { useEffect, useState, type ElementType } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { ChevronDown, FileText, ShieldCheck, X } from "lucide-react";
import { navigationItems, type NavigationItem } from "@/app/navigation";
import { useAuth } from "@/modules/identity/context/AuthContext";

interface AppSidebarProps { open: boolean; onClose: () => void; }

export default function AppSidebar({ open, onClose }: AppSidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const [expanded, setExpanded] = useState<string[]>(["identity","organization","accounting"]);
  const canManageLegal = Boolean(user?.is_platform_admin || user?.is_superuser);
  const items = navigationItems.filter((item) => item.visible !== false);
  const isActive = (path?: string) => Boolean(path && (location.pathname === path || location.pathname.startsWith(path + "/")));

  useEffect(() => {
    const activeParents = items.filter((item) => item.children?.some((child) => isActive(child.path))).map((item) => item.id);
    if (activeParents.length) setExpanded((current) => Array.from(new Set([...current, ...activeParents])));
  }, [location.pathname]);

  const renderItem = (item: NavigationItem) => {
    const Icon = item.icon as ElementType | undefined;
    if (item.type === "item" && item.path) {
      return <NavLink key={item.id} to={item.path} onClick={onClose} className={({isActive: active}) => "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all " + (active ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" : "text-slate-600 hover:bg-slate-100 hover:text-slate-950")}><span className="flex size-8 items-center justify-center rounded-lg bg-current/5"><Icon className="size-4.5"/></span><span className="truncate">{item.labelAr}</span></NavLink>;
    }
    if (item.type !== "group") return null;
    const opened = expanded.includes(item.id);
    const active = item.children?.some((child) => isActive(child.path));
    return <div key={item.id} className="space-y-1">
      <button type="button" onClick={() => setExpanded((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current,item.id])} className={"flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm font-semibold transition " + (active ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100")}><span className="flex items-center gap-3"><span className="flex size-8 items-center justify-center rounded-lg bg-slate-100"><Icon className="size-4.5"/></span>{item.labelAr}</span><ChevronDown className={"size-4 transition-transform " + (opened ? "rotate-180" : "")}/></button>
      <div className={(opened ? "max-h-[600px] opacity-100" : "max-h-0 opacity-0") + " overflow-hidden transition-all duration-300"}><div className="mr-5 space-y-1 border-r border-slate-200 pr-3">{item.children?.map(renderItem)}</div></div>
    </div>;
  };

  return <>
    {open && <button type="button" aria-label="إغلاق القائمة" className="fixed inset-0 z-40 bg-slate-950/35 backdrop-blur-sm lg:hidden" onClick={onClose}/>}
    <aside className={"fixed right-0 top-0 z-50 flex h-screen w-[280px] flex-col border-l border-slate-200 bg-white shadow-2xl shadow-slate-900/5 transition-transform duration-300 " + (open ? "translate-x-0" : "translate-x-full") + " lg:translate-x-0"}>
      <div className="border-b border-slate-100 px-5 py-5"><div className="flex items-center gap-3"><div className="flex size-11 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-600 text-white shadow-lg shadow-blue-600/20"><span className="text-lg font-black">P</span></div><div className="min-w-0"><p className="text-lg font-black tracking-tight text-slate-950">PrimeERP</p><p className="truncate text-[11px] font-medium text-slate-400">Enterprise Resource Planning</p></div><button type="button" className="mr-auto rounded-lg p-2 hover:bg-slate-100 lg:hidden" onClick={onClose}><X className="size-4"/></button></div></div>
      <div className="px-4 pt-4"><div className="rounded-2xl bg-slate-950 px-4 py-3 text-white"><p className="text-[10px] font-black uppercase tracking-[0.18em] text-blue-300">Workspace</p><p className="mt-1 truncate text-sm font-bold">{user?.tenant_name || "Platform Administration"}</p><p className="mt-0.5 text-xs text-slate-400">{user?.tenant_slug ? "/" + user.tenant_slug : "Central workspace"}</p></div></div>
      <nav className="flex-1 overflow-y-auto px-3 py-4"><p className="mb-2 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">Modules</p><div className="space-y-1">{items.map(renderItem)}{canManageLegal && <NavLink to="/settings/legal" onClick={onClose} className={({isActive:active}) => "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold " + (active ? "bg-blue-600 text-white" : "text-slate-600 hover:bg-slate-100")}><span className="flex size-8 items-center justify-center rounded-lg bg-current/5"><FileText className="size-4.5"/></span>المستندات القانونية</NavLink>}</div></nav>
      <div className="border-t border-slate-100 p-4"><div className="flex items-center gap-2 rounded-2xl bg-slate-50 px-4 py-3"><ShieldCheck className="size-4 text-blue-600"/><div><p className="text-xs font-bold text-slate-700">{canManageLegal ? "Super Admin" : "Workspace User"}</p><p className="mt-1 text-[11px] text-slate-400">Secure enterprise workspace</p></div></div></div>
    </aside>
  </>;
}
