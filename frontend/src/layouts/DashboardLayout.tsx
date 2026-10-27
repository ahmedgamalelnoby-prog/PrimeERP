import { useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AppWindow, ShieldCheck } from "lucide-react";
import AppHeader from "@/components/layout/AppHeader";
import AppSidebar from "@/components/layout/AppSidebar";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();
  const { i18n } = useTranslation();
  const isArabic = i18n.resolvedLanguage?.startsWith("ar") ?? true;

  return <div className="min-h-screen bg-background text-foreground" dir={isArabic ? "rtl" : "ltr"}>
    <AppSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
    <div className={["min-h-screen", isArabic ? "lg:mr-[286px]" : "lg:ml-[286px]"].join(" ")}>
      <AppHeader onMenuClick={() => setSidebarOpen(true)} />
      <main key={location.pathname} className="min-h-[calc(100vh-78px)] px-4 py-5 sm:px-6 sm:py-7 xl:px-8">
        <div className="mx-auto w-full max-w-[1680px]"><Outlet /></div>
        <footer className="mx-auto mt-10 flex max-w-[1680px] flex-col gap-2 border-t border-border/80 pt-5 text-[11px] text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2"><AppWindow className="h-3.5 w-3.5" /><span>PrimeERP · {isArabic ? "منصة إدارة موارد المؤسسة" : "Enterprise Resource Planning"}</span></div>
          <div className="flex items-center gap-2"><ShieldCheck className="h-3.5 w-3.5 text-emerald-600" /><span>{isArabic ? "تُطبّق الصلاحيات على مستوى المؤسسة والموديول" : "Permissions are enforced at organization and module level"}</span></div>
        </footer>
      </main>
    </div>
  </div>;
}
