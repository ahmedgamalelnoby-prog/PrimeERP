import { useEffect, useMemo, useState } from "react";
import type { ElementType } from "react";

import {
  BarChart3,
  Building2,
  Calculator,
  ChevronDown,
  ClipboardList,
  FileText,
  GitBranch,
  LayoutDashboard,
  List,
  Package,
  ShieldCheck,
  ShoppingCart,
  UserRound,
  Users,
  Warehouse,
  X,
} from "lucide-react";

import {
  NavLink,
  useLocation,
} from "react-router-dom";

import { useAuth } from "@/modules/identity/context/AuthContext";
import { usePermissions } from "@/modules/identity/hooks/usePermissions";

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
}

interface SubMenuItem {
  title: string;
  path: string;
  icon: ElementType;
  permission?: string;
  module?: string;
}

interface MenuItem {
  title: string;
  icon: ElementType;
  path?: string;
  children?: SubMenuItem[];
  permission?: string;
  module?: string;
}

const menuItems: MenuItem[] = [
  {
    title: "لوحة التحكم",
    icon: LayoutDashboard,
    children: [
      { title: "الرئيسية", path: "/dashboard", icon: LayoutDashboard },
    ],
  },
  {
    title: "المستخدمون",
    icon: Users,
    children: [
      { title: "قائمة المستخدمين", path: "/users", icon: List, permission: "users.access" },
      { title: "الأدوار والصلاحيات", path: "/roles", icon: ShieldCheck, permission: "users.access" },
    ],
  },
  {
    title: "الشركات",
    module: "enterprise",
    permission: "company.access",
    icon: Building2,
    children: [
      { title: "قائمة الشركات", path: "/companies", icon: List, permission: "company.access" },
      { title: "الفروع", path: "/branches", icon: GitBranch, permission: "company.access" },
    ],
  },
  {
    title: "العملاء",
    module: "sales",
    permission: "commerce.access",
    icon: UserRound,
    children: [
      { title: "قائمة العملاء", path: "/customers", icon: List, permission: "commerce.access" },
    ],
  },
  {
    title: "المنتجات",
    module: "inventory",
    permission: "inventory.access",
    icon: Package,
    children: [
      { title: "قائمة المنتجات", path: "/products", icon: List, permission: "inventory.access" },
    ],
  },
  {
    title: "المخزون",
    module: "inventory",
    permission: "inventory.access",
    icon: Warehouse,
    children: [
      { title: "نظرة عامة", path: "/inventory", icon: Warehouse, permission: "inventory.access" },
      { title: "المخازن", path: "/inventory/warehouses", icon: Building2, permission: "inventory.access" },
    ],
  },
  {
    title: "الحسابات",
    module: "accounting",
    permission: "accounting.access",
    icon: Calculator,
    children: [
      { title: "نظرة عامة", path: "/accounting", icon: Calculator, permission: "accounting.access" },
      { title: "دليل الحسابات", path: "/accounting/chart-of-accounts", icon: List, permission: "accounting.access" },
      { title: "القيود اليومية", path: "/accounting/journal-entries", icon: FileText, permission: "accounting.access" },
      { title: "التقارير المالية", path: "/accounting/reports", icon: BarChart3, permission: "accounting.access" },
    ],
  },
  {
    title: "المبيعات",
    module: "sales",
    permission: "commerce.access",
    icon: ShoppingCart,
    children: [
      { title: "الطلبات", path: "/sales/orders", icon: ClipboardList, permission: "commerce.access" },
    ],
  },
];

export default function AppSidebar({
  open,
  onClose,
}: AppSidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const { hasPermission, hasModule } = usePermissions();

  const [expandedMenus, setExpandedMenus] =
    useState<string[]>([]);

  const visibleMenuItems = useMemo(
    () => menuItems
      .map((item) => ({
        ...item,
        children: item.children?.filter((child) =>
          (!child.permission || hasPermission(child.permission)) &&
          (!child.module || hasModule(child.module)),
        ),
      }))
      .filter((item) =>
        Boolean(item.children?.length) &&
        (!item.permission || hasPermission(item.permission)) &&
        (!item.module || hasModule(item.module)),
      ),
    [hasPermission, hasModule, user?.id],
  );

  useEffect(() => {
    const activeParents = visibleMenuItems
      .filter((item) =>
        item.children?.some((child) =>
          location.pathname.startsWith(child.path),
        ),
      )
      .map((item) => item.title);

    setExpandedMenus((current) =>
      Array.from(
        new Set([
          ...current,
          ...activeParents,
        ]),
      ),
    );
  }, [location.pathname, visibleMenuItems]);

  const toggleMenu = (title: string) => {
    setExpandedMenus((current) =>
      current.includes(title)
        ? current.filter(
            (menuTitle) =>
              menuTitle !== title,
          )
        : [...current, title],
    );
  };

  const isChildActive = (
    children?: SubMenuItem[],
  ) =>
    children?.some((child) =>
      location.pathname.startsWith(child.path),
    ) ?? false;

  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="إغلاق القائمة"
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={[
          "fixed right-0 top-0 z-50 h-screen w-72",
          "border-l bg-card shadow-xl",
          "transition-transform duration-300",
          open
            ? "translate-x-0"
            : "translate-x-full",
          "lg:translate-x-0",
        ].join(" ")}
      >
        <div className="flex h-16 items-center justify-between border-b px-5">
          <div>
            <h1 className="text-xl font-bold">
              PrimeERP
            </h1>

            <p className="text-xs text-muted-foreground">
              Enterprise Resource Planning
            </p>
          </div>

          <button
            type="button"
            className="rounded-lg p-2 transition-colors hover:bg-muted lg:hidden"
            onClick={onClose}
            aria-label="إغلاق القائمة"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="h-[calc(100vh-4rem)] overflow-y-auto p-4">
          <p className="mb-3 px-3 text-xs font-semibold text-muted-foreground">
            القائمة الرئيسية
          </p>

          <div className="space-y-1">
            {visibleMenuItems.map((item) => {
              const Icon = item.icon;
              const expanded =
                expandedMenus.includes(
                  item.title,
                );
              const childActive =
                isChildActive(item.children);

              return (
                <div
                  key={item.title}
                  className="space-y-1"
                >
                  <button
                    type="button"
                    onClick={() =>
                      toggleMenu(item.title)
                    }
                    className={[
                      "flex w-full items-center justify-between rounded-xl px-3 py-2.5",
                      "text-sm font-medium transition-all duration-200",
                      childActive
                        ? "bg-primary/10 text-primary"
                        : "text-foreground hover:bg-muted",
                    ].join(" ")}
                  >
                    <div className="flex items-center gap-3">
                      <Icon className="h-5 w-5" />
                      <span>{item.title}</span>
                    </div>

                    <ChevronDown
                      className={[
                        "h-4 w-4 transition-transform duration-300",
                        expanded
                          ? "rotate-180"
                          : "",
                      ].join(" ")}
                    />
                  </button>

                  <div
                    className={[
                      "grid overflow-hidden transition-all duration-300",
                      expanded
                        ? "grid-rows-[1fr] opacity-100"
                        : "grid-rows-[0fr] opacity-0",
                    ].join(" ")}
                  >
                    <div className="min-h-0">
                      <div className="mr-5 mt-1 space-y-1 border-r pr-3">
                        {item.children?.map(
                          (child) => {
                            const ChildIcon =
                              child.icon;

                            return (
                              <NavLink
                                key={child.path}
                                to={child.path}
                                onClick={onClose}
                                className={({
                                  isActive,
                                }) =>
                                  [
                                    "flex items-center gap-3 rounded-lg px-3 py-2",
                                    "text-sm transition-all duration-200",
                                    isActive
                                      ? "bg-primary text-primary-foreground shadow-sm"
                                      : "text-muted-foreground hover:bg-muted hover:text-foreground",
                                  ].join(" ")
                                }
                              >
                                <ChildIcon className="h-4 w-4" />
                                <span>
                                  {child.title}
                                </span>
                              </NavLink>
                            );
                          },
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </nav>
      </aside>
    </>
  );
}