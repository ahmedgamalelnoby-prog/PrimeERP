import { useState } from "react";
import { Outlet } from "react-router-dom";
import AppHeader from "@/components/layout/AppHeader";
import AppSidebar from "@/components/layout/AppSidebar";

export default function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,0.08),transparent_32%),linear-gradient(180deg,#f8fafc_0%,#f1f5f9_100%)]" dir="rtl">
      <AppSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="min-h-screen lg:mr-[280px]">
        <AppHeader onMenuClick={() => setSidebarOpen(true)} />
        <main className="p-4 sm:p-6 xl:p-8"><Outlet /></main>
      </div>
    </div>
  );
}
