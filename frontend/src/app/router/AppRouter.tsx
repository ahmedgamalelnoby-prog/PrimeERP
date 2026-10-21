import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "@/modules/identity/hooks/useAuth";

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

function ComingSoonPage({ title }: { title: string }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center" dir="rtl">
      <div className="w-full max-w-lg rounded-2xl border bg-card p-8 text-center shadow-sm">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="mt-3 text-sm text-muted-foreground">هذه الصفحة تحت التطوير وسيتم ربطها لاحقًا.</p>
      </div>
    </div>
  );
}

function SuperAdminRoute() {
  const { user, isLoading } = useAuth();
  if (isLoading) return null;
  if (!user || (!user.is_platform_admin && !user.is_superuser)) return <Navigate to="/dashboard" replace />;
  return <LegalManagementPage />;
}

export default function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/register" element={<PublicRoute><RegisterPage /></PublicRoute>} />
      <Route path="/login" element={<PublicRoute><LoginPage /></PublicRoute>} />

      {/* المستندات القانونية متاحة قبل تسجيل الدخول */}
      <Route path="/terms" element={<LegalDocumentPage />} />
      <Route path="/privacy" element={<LegalDocumentPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<DashboardLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/dashboard/reports" element={<ComingSoonPage title="التقارير المختصرة" />} />

          <Route path="/users" element={<UsersPage />} />
          <Route path="/users/new" element={<ComingSoonPage title="إضافة مستخدم" />} />
          <Route path="/roles" element={<RolesPage />} />
          <Route path="/permissions" element={<PermissionsPage />} />

          <Route path="/identity/users" element={<Navigate to="/users" replace />} />
          <Route path="/identity/roles" element={<Navigate to="/roles" replace />} />
          <Route path="/identity/permissions" element={<Navigate to="/permissions" replace />} />

          {/* إدارة المستندات القانونية — صلاحية التعديل يتم فرضها من الـ API */}
          <Route path="/settings/legal" element={<SuperAdminRoute />} />

          <Route path="/companies" element={<ComingSoonPage title="قائمة الشركات" />} />
          <Route path="/companies/new" element={<ComingSoonPage title="إضافة شركة" />} />
          <Route path="/companies/settings" element={<ComingSoonPage title="إعدادات الشركات" />} />
          <Route path="/branches" element={<ComingSoonPage title="الفروع" />} />

          <Route path="/customers" element={<ComingSoonPage title="قائمة العملاء" />} />
          <Route path="/customers/new" element={<ComingSoonPage title="إضافة عميل" />} />
          <Route path="/customers/reports" element={<ComingSoonPage title="تقارير العملاء" />} />

          <Route path="/products" element={<ComingSoonPage title="قائمة المنتجات" />} />
          <Route path="/products/new" element={<ComingSoonPage title="إضافة منتج" />} />
          <Route path="/products/categories" element={<ComingSoonPage title="تصنيفات المنتجات" />} />
          <Route path="/products/units" element={<ComingSoonPage title="وحدات القياس" />} />

          <Route path="/inventory" element={<ComingSoonPage title="نظرة عامة على المخزون" />} />
          <Route path="/inventory/warehouses" element={<ComingSoonPage title="المخازن" />} />
          <Route path="/inventory/movements" element={<ComingSoonPage title="حركات المخزون" />} />
          <Route path="/inventory/reports" element={<ComingSoonPage title="تقارير المخزون" />} />

          <Route path="/accounting" element={<ComingSoonPage title="نظرة عامة على الحسابات" />} />
          <Route path="/accounting/chart-of-accounts" element={<ComingSoonPage title="دليل الحسابات" />} />
          <Route path="/accounting/journal-entries" element={<ComingSoonPage title="القيود اليومية" />} />
          <Route path="/accounting/reports" element={<ComingSoonPage title="التقارير المالية" />} />

          <Route path="/sales/orders" element={<ComingSoonPage title="طلبات المبيعات" />} />
          <Route path="/sales/orders/new" element={<ComingSoonPage title="إضافة طلب" />} />
          <Route path="/sales/reports" element={<ComingSoonPage title="تقارير المبيعات" />} />

          <Route path="*" element={<ComingSoonPage title="الصفحة غير موجودة" />} />
        </Route>
      </Route>
    </Routes>
  );
}
