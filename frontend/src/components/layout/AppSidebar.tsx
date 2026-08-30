import { useEffect, useState } from "react";
import type { ElementType } from "react";

import {
  BarChart3,
  Building2,
  Calculator,
  ChevronDown,
  PlusCircle,
  ClipboardList,
  FileText,
  GitBranch,
  LayoutDashboard,
  List,
  Package,
  Settings,
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

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
}

interface SubMenuItem {
  title: string;
  path: string;
  icon: ElementType;
}

interface MenuItem {
  title: string;
  icon: ElementType;
  path?: string;
  children?: SubMenuItem[];
}

const menuItems: MenuItem[] = [
  {
    title: "لوحة التحكم",
    icon: LayoutDashboard,
    children: [
      {
        title: "الرئيسية",
        path: "/dashboard",
        icon: LayoutDashboard,
      },
      {
        title: "التقارير المختصرة",
        path: "/dashboard/reports",
        icon: BarChart3,
      },
    ],
  },
  {
    title: "المستخدمون",
    icon: Users,
    children: [
      {
        title: "قائمة المستخدمين",
        path: "/users",
        icon: List,
      },
      {
        title: "إضافة مستخدم",
        path: "/users/new",
        icon: PlusCircle,
      },
      {
        title: "الأدوار والصلاحيات",
        path: "/roles",
        icon: ShieldCheck,
      },
    ],
  },
  {
    title: "الشركات",
    icon: Building2,
    children: [
      {
        title: "قائمة الشركات",
        path: "/companies",
        icon: List,
      },
      {
        title: "إضافة شركة",
        path: "/companies/new",
        icon: PlusCircle,
      },
      {
        title: "الفروع",
        path: "/branches",
        icon: GitBranch,
      },
      {
        title: "إعدادات الشركات",
        path: "/companies/settings",
        icon: Settings,
      },
    ],
  },
  {
    title: "العملاء",
    icon: UserRound,
    children: [
      {
        title: "قائمة العملاء",
        path: "/customers",
        icon: List,
      },
      {
        title: "إضافة عميل",
        path: "/customers/new",
        icon: PlusCircle,
      },
      {
        title: "تقارير العملاء",
        path: "/customers/reports",
        icon: FileText,
      },
    ],
  },
  {
    title: "المنتجات",
    icon: Package,
    children: [
      {
        title: "قائمة المنتجات",
        path: "/products",
        icon: List,
      },
      {
        title: "إضافة منتج",
        path: "/products/new",
        icon: PlusCircle,
      },
      {
        title: "التصنيفات",
        path: "/products/categories",
        icon: ClipboardList,
      },
      {
        title: "وحدات القياس",
        path: "/products/units",
        icon: Settings,
      },
    ],
  },
  {
    title: "المخزون",
    icon: Warehouse,
    children: [
      {
        title: "نظرة عامة",
        path: "/inventory",
        icon: Warehouse,
      },
      {
        title: "المخازن",
        path: "/inventory/warehouses",
        icon: Building2,
      },
      {
        title: "حركات المخزون",
        path: "/inventory/movements",
        icon: ClipboardList,
      },
      {
        title: "تقارير المخزون",
        path: "/inventory/reports",
        icon: BarChart3,
      },
    ],
  },
  {
    title: "الحسابات",
    icon: Calculator,
    children: [
      {
        title: "نظرة عامة",
        path: "/accounting",
        icon: Calculator,
      },
      {
        title: "دليل الحسابات",
        path: "/accounting/chart-of-accounts",
        icon: List,
      },
      {
        title: "القيود اليومية",
        path: "/accounting/journal-entries",
        icon: FileText,
      },
      {
        title: "التقارير المالية",
        path: "/accounting/reports",
        icon: BarChart3,
      },
    ],
  },
  {
    title: "المبيعات",
    icon: ShoppingCart,
    children: [
      {
        title: "الطلبات",
        path: "/sales/orders",
        icon: ClipboardList,
      },
      {
        title: "إضافة طلب",
        path: "/sales/orders/new",
        icon: PlusCircle,
      },
      {
        title: "تقارير المبيعات",
        path: "/sales/reports",
        icon: BarChart3,
      },
    ],
  },
];

export default function AppSidebar({
  open,
  onClose,
}: AppSidebarProps) {
  const location = useLocation();

  const [expandedMenus, setExpandedMenus] =
    useState<string[]>([]);

  useEffect(() => {
    const activeParents = menuItems
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
  }, [location.pathname]);

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
            {menuItems.map((item) => {
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