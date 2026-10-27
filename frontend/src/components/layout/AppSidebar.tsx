import { useEffect, useMemo, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Activity, ChevronDown, Command, Search, ShieldCheck, X } from "lucide-react";
import { getVisibleNavigationItems, isNavigationItemActive, type NavigationItem } from "@/app/navigation";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/modules/identity/hooks/useAuth";

interface AppSidebarProps { open: boolean; onClose: () => void; }

function filterNavigation(items: NavigationItem[], query: string): NavigationItem[] {
  if (!query.trim()) return items;
  const normalized = query.trim().toLocaleLowerCase();
  return items.flatMap((item) => {
    const matchingChildren = item.children ? filterNavigation(item.children, query) : [];
    const matches = [item.label, item.labelAr, item.id].some((value) => value.toLocaleLowerCase().includes(normalized));
    if (item.children?.length) return matches ? [{ ...item, children: item.children }] : matchingChildren.length ? [{ ...item, children: matchingChildren }] : [];
    return matches ? [item] : [];
  });
}

function NavigationNode({ item, pathname, onNavigate, forceExpanded, depth, isArabic, openTopGroup, setOpenTopGroup }: {
  item: NavigationItem; pathname: string; onNavigate: () => void; forceExpanded: boolean; depth: number; isArabic: boolean;
  openTopGroup: string | null; setOpenTopGroup: (id: string | null) => void;
}) {
  const [expanded, setExpanded] = useState(isNavigationItemActive(item, pathname));
  const Icon = item.icon;
  const hasChildren = Boolean(item.children?.length);
  const active = isNavigationItemActive(item, pathname);
  const isTopLevel = depth === 0;
  const isExpanded = forceExpanded || (isTopLevel ? openTopGroup === item.id : expanded);

  useEffect(() => {
    if (active && !isTopLevel) setExpanded(true);
  }, [active, isTopLevel]);

  if (item.type === "separator") return <div className="my-3 border-t border-white/10" />;
  if (hasChildren) {
    return <div className="space-y-1">
      <button type="button" aria-expanded={isExpanded} onClick={() => {
        if (isTopLevel) setOpenTopGroup(openTopGroup === item.id ? null : item.id);
        else setExpanded((value) => !value);
      }} className={["group flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
        active ? "bg-white/10 text-white" : "text-slate-300 hover:bg-white/[0.07] hover:text-white"].join(" ")}>
        <span className="flex min-w-0 items-center gap-3">{Icon && <Icon className="h-[18px] w-[18px] shrink-0 text-slate-400 group-hover:text-cyan-300" />}<span className="truncate">{isArabic ? item.labelAr : item.label}</span></span>
        <ChevronDown className={["h-4 w-4 shrink-0 text-slate-500 transition-transform", isExpanded ? "rotate-180" : ""].join(" ")} />
      </button>
      {isExpanded && <div className="mr-4 space-y-1 border-r border-white/10 pr-3">
        {item.children?.map((child) => <NavigationNode key={child.id} item={child} pathname={pathname} onNavigate={onNavigate} forceExpanded={forceExpanded} depth={depth + 1} isArabic={isArabic} openTopGroup={openTopGroup} setOpenTopGroup={setOpenTopGroup} />)}
      </div>}
    </div>;
  }
  if (!item.path) return null;
  return <NavLink to={item.path} onClick={onNavigate} className={({ isActive }) => [
    "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all",
    isActive ? "bg-gradient-to-l from-cyan-400/20 to-blue-500/20 text-white ring-1 ring-inset ring-cyan-300/25 shadow-lg shadow-slate-950/10" : "text-slate-300 hover:bg-white/[0.07] hover:text-white",
  ].join(" ")}>
    {Icon && <Icon className="h-[18px] w-[18px] shrink-0 text-slate-400 transition-colors group-hover:text-cyan-300" />}
    <span className="truncate">{isArabic ? item.labelAr : item.label}</span>
    {item.isNew && <span className="mr-auto rounded-full border border-cyan-300/20 bg-cyan-300/10 px-1.5 py-0.5 text-[9px] font-bold text-cyan-200">{isArabic ? "جديد" : "New"}</span>}
  </NavLink>;
}

export default function AppSidebar({ open, onClose }: AppSidebarProps) {
  const location = useLocation();
  const { i18n } = useTranslation();
  const isArabic = i18n.resolvedLanguage?.startsWith("ar") ?? true;
  const { user } = useAuth();
  const [search, setSearch] = useState("");
  const [openTopGroup, setOpenTopGroup] = useState<string | null>(null);
  const navigation = useMemo(() => filterNavigation(
    getVisibleNavigationItems(user?.enabled_modules ?? [], Boolean(user?.is_platform_admin || user?.is_superuser)), search,
  ), [user?.enabled_modules, user?.is_platform_admin, user?.is_superuser, search]);
  const isPlatformAdmin = Boolean(user?.is_platform_admin || user?.is_superuser);

  useEffect(() => {
    const activeGroup = navigation.find((item) => item.children?.length && isNavigationItemActive(item, location.pathname));
    if (activeGroup) setOpenTopGroup(activeGroup.id);
  }, [location.pathname, navigation]);

  return <>
    {open && <button type="button" aria-label={isArabic ? "إغلاق القائمة" : "Close navigation"} className="fixed inset-0 z-40 bg-slate-950/60 backdrop-blur-sm lg:hidden" onClick={onClose} />}
    <aside className={["fixed top-0 z-50 flex h-screen w-[286px] flex-col overflow-hidden border-slate-800 bg-[#0b1730] text-white shadow-2xl shadow-slate-950/20 transition-transform duration-300", isArabic ? "right-0 border-l" : "left-0 border-r", open ? "translate-x-0" : isArabic ? "translate-x-full" : "-translate-x-full", "lg:translate-x-0"].join(" ")}>
      <div className="relative overflow-hidden border-b border-white/10 px-5 pb-5 pt-5">
        <div className="absolute -left-10 -top-14 h-32 w-32 rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="relative flex items-center justify-between gap-3">
          <div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-200/20 bg-gradient-to-br from-blue-500 to-cyan-400 shadow-lg shadow-blue-950/40"><Command className="h-6 w-6 text-white" /></div>
            <div><div className="text-xl font-black tracking-tight">Prime<span className="text-cyan-300">ERP</span></div><div className="mt-0.5 text-[10px] font-semibold tracking-[0.16em] text-slate-400">BUSINESS OPERATING SYSTEM</div></div>
          </div>
          <button type="button" className="rounded-lg p-2 text-slate-400 transition-colors hover:bg-white/10 hover:text-white lg:hidden" onClick={onClose} aria-label={isArabic ? "إغلاق القائمة" : "Close navigation"}><X className="h-5 w-5" /></button>
        </div>
        <div className="mt-5 flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2"><Activity className="h-4 w-4 text-emerald-300" /><span className="text-xs font-medium text-slate-300">{isArabic ? "مساحة العمل" : "Workspace"}</span><span className="mr-auto flex items-center gap-1.5 text-[10px] text-emerald-300"><span className="h-1.5 w-1.5 rounded-full bg-emerald-400" /> {isArabic ? "متصل" : "Online"}</span></div>
      </div>
      <div className="px-4 pb-3 pt-4"><label htmlFor="primeerp-navigation-search" className="sr-only">{isArabic ? "ابحث في القائمة" : "Search navigation"}</label><div className="relative">
        <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
        <Input id="primeerp-navigation-search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder={isArabic ? "ابحث عن شاشة أو موديول..." : "Search screens or modules..."} className="h-10 border-white/10 bg-white/[0.06] pr-9 text-xs text-white placeholder:text-slate-500 focus-visible:ring-cyan-400/50" />
        {search && <button type="button" aria-label={isArabic ? "مسح البحث" : "Clear search"} onClick={() => setSearch("")} className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-white"><X className="h-3.5 w-3.5" /></button>}
      </div></div>
      <nav aria-label={isArabic ? "القائمة الرئيسية" : "Main navigation"} className="min-h-0 flex-1 overflow-y-auto px-3 pb-4 pt-1 [scrollbar-color:rgba(148,163,184,.25)_transparent] [scrollbar-width:thin]">
        <p className="mb-3 px-3 text-[10px] font-bold tracking-[0.16em] text-slate-500">{search ? (isArabic ? "نتائج البحث" : "Search results") : (isArabic ? "إدارة الأعمال" : "Business management")}</p>
        <div className="space-y-1">{navigation.map((item) => <NavigationNode key={item.id} item={item} pathname={location.pathname} onNavigate={onClose} forceExpanded={Boolean(search)} depth={0} isArabic={isArabic} openTopGroup={openTopGroup} setOpenTopGroup={setOpenTopGroup} />)}
          {navigation.length === 0 && <p className="rounded-xl border border-dashed border-white/10 px-3 py-5 text-center text-xs text-slate-500">{isArabic ? "لا توجد نتائج مطابقة." : "No matching results."}</p>}</div>
      </nav>
      <div className="border-t border-white/10 p-4"><div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.04] p-3"><div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-blue-400/10 text-cyan-200"><ShieldCheck className="h-5 w-5" /></div><div className="min-w-0"><p className="truncate text-xs font-bold text-slate-200">{isPlatformAdmin ? (isArabic ? "مسؤول المنصة" : "Platform administrator") : (isArabic ? "مساحة مؤسسية آمنة" : "Secure workspace")}</p><p className="mt-1 text-[10px] text-slate-500">{isArabic ? "صلاحيات وعزل بيانات حسب المؤسسة" : "Organization-level access and data isolation"}</p></div></div><p className="mt-3 text-center text-[9px] tracking-wide text-slate-600">PrimeERP • Enterprise Suite</p></div>
    </aside>
  </>;
}
