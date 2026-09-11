import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "./ProtectedRoute";
import PublicRoute from "./PublicRoute";
import DashboardLayout from "@/layouts/DashboardLayout";
import LoginPage from "@/modules/identity/pages/LoginPage";
import LandingPage from "@/modules/public/pages/LandingPage";
import RegisterPage from "@/modules/public/pages/RegisterPage";
import PermissionsPage from "@/modules/identity/pages/PermissionsPage";
import DashboardPage from "@/modules/platform/pages/DashboardPage";
import UsersPage from "@/modules/users/pages/UsersPage";
import RolesPage from "@/modules/roles/pages/RolesPage";
import LegalDocumentPage from "@/modules/legal/pages/LegalDocumentPage";
import LegalManagementPage from "@/modules/legal/pages/LegalManagementPage";
import PlansPage from "@/modules/platform/plans/PlansPage";
import AccountingPage from "@/modules/accounting/pages/AccountingPage";
import AccountsPage from "@/modules/accounting/chart-of-accounts/AccountsPage";

function ComingSoonPage({ title }: { title: string }) {
  return <div className="flex min-h-[60vh] items-center justify-center" dir="rtl"><div className="w-full max-w-lg rounded-2xl border bg-card p-8 text-center shadow-sm"><h1 className="text-2xl font-bold">{title}</h1><p className="mt-3 text-sm text-muted-foreground">هذه الصفحة لم تُربط بعد بوظائفها النهائية.</p></div></div>;
}

export default function AppRouter() {
  return <Routes>
    <Route path="/" element={<LandingPage />} />
    <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
    <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />
    <Route path="/terms" element={<LegalDocumentPage />} />
    <Route path="/privacy" element={<LegalDocumentPage />} />
    <Route element={<ProtectedRoute />}>
      <Route element={<DashboardLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="/roles" element={<RolesPage />} />
        <Route path="/permissions" element={<PermissionsPage />} />
        <Route path="/identity/users" element={<Navigate to="/users" replace />} />
        <Route path="/identity/roles" element={<Navigate to="/roles" replace />} />
        <Route path="/identity/permissions" element={<Navigate to="/permissions" replace />} />
        <Route path="/settings/legal" element={<LegalManagementPage />} />
        <Route path="/platform/plans" element={<PlansPage />} />
        <Route path="/accounting" element={<AccountingPage />} />
        <Route path="/accounting/chart-of-accounts" element={<AccountsPage />} />
        <Route path="/accounting/journal-entries" element={<ComingSoonPage title="القيود اليومية" />} />
        <Route path="/accounting/reports" element={<ComingSoonPage title="التقارير المالية" />} />
        <Route path="/companies" element={<ComingSoonPage title="الشركات" />} />
        <Route path="/branches" element={<ComingSoonPage title="الفروع" />} />
        <Route path="/customers" element={<ComingSoonPage title="العملاء" />} />
        <Route path="/products" element={<ComingSoonPage title="المنتجات" />} />
        <Route path="/inventory" element={<ComingSoonPage title="المخزون" />} />
        <Route path="/sales/orders" element={<ComingSoonPage title="طلبات المبيعات" />} />
        <Route path="*" element={<ComingSoonPage title="الصفحة غير موجودة" />} />
      </Route>
    </Route>
  </Routes>;
}
