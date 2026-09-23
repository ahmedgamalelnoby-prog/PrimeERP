import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "@/modules/identity/hooks/useAuth";

const CORE_PATHS = ["/dashboard", "/users", "/roles", "/permissions", "/identity", "/companies", "/branches", "/settings", "/helpdesk"];
const PLATFORM_PATHS = ["/modules", "/saas", "/platform/plans", "/developer"];

const PREFIX_TO_MODULE: Array<[string, string]> = [
  ["/accounting", "accounting"],
  ["/inventory", "inventory"],
  ["/products", "inventory"],
  ["/sales", "sales"],
  ["/customers", "sales"],
  ["/purchases", "purchasing"],
  ["/purchasing", "purchasing"],
  ["/shipping", "shipping"],
  ["/crm", "crm"],
  ["/hr", "hr"],
  ["/pos", "pos"],
  ["/manufacturing", "manufacturing"],
  ["/commercial-leasing", "commercial_leasing"],
  ["/hospitality", "hospitality"],
  ["/reports", "reports"],
  ["/enterprise", "enterprise"],
  ["/mobile", "mobile"],
  ["/commerce", "commerce"],
];

function matchesPath(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(prefix + "/");
}

function AccessDenied({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6" dir="rtl">
      <div className="w-full max-w-lg rounded-3xl border bg-white p-8 text-center shadow-sm">
        <div className="mx-auto flex size-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">403</div>
        <h1 className="mt-5 text-2xl font-black">{title}</h1>
        <p className="mt-3 text-sm leading-7 text-slate-500">{detail}</p>
      </div>
    </div>
  );
}

export default function EntitlementGuard() {
  const location = useLocation();
  const { user } = useAuth();

  if (!user) return null;

  const pathname = location.pathname;
  const isPlatformAdmin = Boolean(user.is_platform_admin || user.is_superuser);

  if (PLATFORM_PATHS.some((path) => matchesPath(pathname, path)) && !isPlatformAdmin) {
    return <AccessDenied title="هذه المنطقة مخصصة لإدارة المنصة" detail="حساب العميل لا يملك صلاحية إدارة كتالوج PrimeERP أو الباقات والاستحقاقات." />;
  }

  if (CORE_PATHS.some((path) => matchesPath(pathname, path)) || pathname === "/") {
    return null;
  }

  const rule = PREFIX_TO_MODULE.find(([prefix]) => matchesPath(pathname, prefix));
  if (!rule || isPlatformAdmin) return null;

  const [_, moduleCode] = rule;
  if (user.enabled_modules?.includes(moduleCode)) return null;

  return (
    <AccessDenied
      title="الموديول غير متاح في باقتك"
      detail={`هذا الموديول غير مفعّل لمساحة عملك الحالية. يمكنك التواصل مع مسؤول الحساب لترقية الباقة أو تفعيل الموديول.`}
    />
  );
}
