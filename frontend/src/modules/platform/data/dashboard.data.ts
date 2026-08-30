import {
  BarChart3,
  Building2,
  FileText,
  GitBranch,
  ShieldCheck,
  Store,
  UserCog,
  Users,
  WalletCards,
} from "lucide-react";

import type {
  BusinessUnit,
  DashboardStatistic,
  QuickAction,
  RecentActivity,
  RevenueOverviewPoint,
} from "../types/dashboard.types";

export const dashboardStatistics: DashboardStatistic[] = [
  {
    id: 1,
    title: "إجمالي المستخدمين",
    value: "24",
    change: 12,
    changeLabel: "مقارنة بالشهر السابق",
    icon: Users,
  },
  {
    id: 2,
    title: "الشركات النشطة",
    value: "4",
    change: 5,
    changeLabel: "مقارنة بالشهر السابق",
    icon: Building2,
  },
  {
    id: 3,
    title: "إجمالي الفروع",
    value: "12",
    change: 8,
    changeLabel: "مقارنة بالشهر السابق",
    icon: GitBranch,
  },
  {
    id: 4,
    title: "إجمالي الإيرادات",
    value: "2.48M EGP",
    change: -3,
    changeLabel: "مقارنة بالشهر السابق",
    icon: WalletCards,
  },
];

export const businessUnits: BusinessUnit[] = [
  {
    id: 1,
    title: "الشركات",
    value: 4,
    icon: Building2,
  },
  {
    id: 2,
    title: "الفروع",
    value: 12,
    icon: GitBranch,
  },
  {
    id: 3,
    title: "الوحدات التجارية",
    value: 35,
    icon: Store,
  },
  {
    id: 4,
    title: "المستخدمون",
    value: 24,
    icon: Users,
  },
];

export const quickActions: QuickAction[] = [
  {
    id: 1,
    title: "إدارة المستخدمين",
    description: "إضافة المستخدمين وتعديل بياناتهم",
    path: "/users",
    icon: UserCog,
  },
  {
    id: 2,
    title: "إدارة الأدوار",
    description: "إدارة الأدوار والصلاحيات",
    path: "/roles",
    icon: ShieldCheck,
  },
  {
    id: 3,
    title: "إدارة الشركات",
    description: "إضافة الشركات وتحديث بياناتها",
    path: "/companies",
    icon: Building2,
  },
  {
    id: 4,
    title: "إدارة الفروع",
    description: "إضافة الفروع وربطها بالشركات",
    path: "/branches",
    icon: GitBranch,
  },
  {
    id: 5,
    title: "العقود",
    description: "متابعة العقود والقيم الإيجارية",
    path: "/contracts",
    icon: FileText,
  },
  {
    id: 6,
    title: "التقارير",
    description: "عرض التقارير المالية والتشغيلية",
    path: "/reports",
    icon: BarChart3,
  },
];

export const recentActivities: RecentActivity[] = [
  {
    id: 1,
    title: "تم إنشاء مستخدم جديد",
    description:
      "تمت إضافة مستخدم جديد وربطه بدور محاسب.",
    time: "منذ 5 دقائق",
    status: "success",
  },
  {
    id: 2,
    title: "تم تحديث بيانات شركة",
    description:
      "تم تعديل البيانات الأساسية للشركة.",
    time: "منذ 20 دقيقة",
    status: "info",
  },
  {
    id: 3,
    title: "محاولة تسجيل دخول غير ناجحة",
    description:
      "تم تسجيل محاولة دخول غير ناجحة لأحد الحسابات.",
    time: "منذ ساعة",
    status: "warning",
  },
  {
    id: 4,
    title: "تم حذف فاتورة",
    description:
      "تم حذف فاتورة وإضافتها إلى سجل المراجعة.",
    time: "منذ ساعتين",
    status: "danger",
  },
];

export const revenueOverview: RevenueOverviewPoint[] = [
  {
    month: "يناير",
    revenue: 48,
    expenses: 30,
  },
  {
    month: "فبراير",
    revenue: 58,
    expenses: 34,
  },
  {
    month: "مارس",
    revenue: 65,
    expenses: 40,
  },
  {
    month: "أبريل",
    revenue: 54,
    expenses: 38,
  },
  {
    month: "مايو",
    revenue: 72,
    expenses: 45,
  },
  {
    month: "يونيو",
    revenue: 82,
    expenses: 49,
  },
  {
    month: "يوليو",
    revenue: 90,
    expenses: 55,
  },
];

export const dashboardDocuments = [
  {
    id: 1,
    title: "الفواتير",
    value: 128,
    icon: FileText,
  },
];