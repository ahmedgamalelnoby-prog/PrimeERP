import { Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/modules/identity/hooks/useAuth";

const CORE_PATHS = ["/dashboard", "/users", "/roles", "/permissions", "/identity", "/companies", "/branches", "/settings", "/helpdesk"];
// The catalog itself is platform administration. Individual /modules/:moduleKey
// workbench routes are tenant module pages and must use normal entitlements.
const PLATFORM_PATHS = ["/modules", "/saas", "/platform/plans", "/developer"];

const PERMISSION_PATHS: Array<[string, string]> = [
  ["/users", "users.view"],
  ["/identity/users", "users.view"],
  ["/roles", "roles.view"],
  ["/identity/roles", "roles.view"],
  ["/permissions", "permissions.view"],
  ["/identity/permissions", "permissions.view"],
  ["/companies", "companies.view"],
  ["/branches", "branches.view"],
  ["/settings", "settings.view"],
  ["/notifications", "company.write"],
  ["/helpdesk", "helpdesk.view"],
  ["/accounting", "accounting.view"],
  ["/treasury", "treasury.view"],
  ["/sales", "sales.view"],
  ["/customers", "customers.view"],
  ["/purchases", "purchase_orders.view"],
  ["/purchasing", "purchase_orders.view"],
  ["/inventory", "inventory.view"],
  ["/products", "products.view"],
  ["/shipping", "shipping.view"],
  ["/crm", "crm.view"],
  ["/hr", "hr.view"],
  ["/pos", "pos.view"],
  ["/manufacturing", "manufacturing.view"],
  ["/commerce", "commerce.view"],
  ["/mobile", "mobile.view"],
  ["/reports", "reports.view"],
  ["/enterprise", "enterprise.view"],
  ["/commercial-leasing", "commercial_leasing.view"],
  ["/hospitality", "hospitality.view"],
];

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
  ["/treasury", "treasury"],
];

const WORKBENCH_ALIASES: Record<string, string> = {
  "cost-centers": "cost_centers",
  cost_centers: "cost_centers",
  einvoice: "einvoice",
  "egyptian-einvoice": "einvoice",
  "time-tracking": "time_tracking",
  time_tracking: "time_tracking",
  "work-orders": "work_orders",
  work_orders: "work_orders",
  "commercial-leasing": "commercial_leasing",
  "real-estate": "real_estate",
  real_estate: "real_estate",
};

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

  if (PLATFORM_PATHS.some((path) => pathname === path || (path !== "/modules" && matchesPath(pathname, path))) && !isPlatformAdmin) {
    return <AccessDenied title="هذه المنطقة مخصصة لإدارة المنصة" detail="حساب العميل لا يملك صلاحية إدارة كتالوج PrimeERP أو الباقات والاستحقاقات." />;
  }

  const permissionRule = PERMISSION_PATHS.find(([prefix]) => matchesPath(pathname, prefix));
  if (permissionRule && !isPlatformAdmin) {
    const [, requiredPermission] = permissionRule;
    if (!user.permissions?.includes(requiredPermission)) {
      return <AccessDenied title="لا تملك الصلاحية المطلوبة" detail="حسابك لا يملك الإذن اللازم لفتح هذه الشاشة. اطلب من مسؤول النظام مراجعة صلاحيات دورك." />;
    }
  }

  if (CORE_PATHS.some((path) => matchesPath(pathname, path)) || pathname === "/") {
    return <Outlet />;
  }

  // Resolve generic workbench pages through the same module entitlement as
  // their dedicated-screen equivalents. Unknown keys fail closed for tenants.
  if (pathname.startsWith("/modules/")) {
    if (isPlatformAdmin) return <Outlet />;
    const rawKey = pathname.slice("/modules/".length).split("/")[0];
    let decodedKey = rawKey;
    try {
      decodedKey = decodeURIComponent(rawKey);
    } catch {
      return <AccessDenied title="الموديول غير معروف" detail="تعذر التحقق من الموديول المطلوب." />;
    }
    const moduleCode = WORKBENCH_ALIASES[decodedKey] || decodedKey.replace(/-/g, "_");
    if (user.enabled_modules?.includes(moduleCode) || user.enabled_modules?.includes(decodedKey)) return <Outlet />;
    return <AccessDenied title="الموديول غير متاح في باقتك" detail="هذا الموديول غير مفعّل لمساحة عملك الحالية، أو أن مفتاحه غير معروف. تواصل مع مسؤول الحساب لتفعيل الموديول." />;
  }

  const rule = PREFIX_TO_MODULE.find(([prefix]) => matchesPath(pathname, prefix));
  if (!rule || isPlatformAdmin) return <Outlet />;

  const [, moduleCode] = rule;
  if (user.enabled_modules?.includes(moduleCode)) return <Outlet />;

  return (
    <AccessDenied
      title="الموديول غير متاح في باقتك"
      detail="هذا الموديول غير مفعّل لمساحة عملك الحالية. يمكنك التواصل مع مسؤول الحساب لترقية الباقة أو تفعيل الموديول."
    />
  );
}
