import { BarChart3, Building2, GitBranch, Users, UserCog, ShieldCheck, FileText } from "lucide-react";
import type { BusinessUnit, QuickAction } from "../types/dashboard.types";

export const buildBusinessUnits = (summary: { users: { total: number }; companies: { total: number }; branches: { total: number } }): BusinessUnit[] => [
  { id: 1, title: "الشركات", value: summary.companies.total, icon: Building2 },
  { id: 2, title: "الفروع", value: summary.branches.total, icon: GitBranch },
  { id: 3, title: "المستخدمون", value: summary.users.total, icon: Users },
];

export const quickActions: QuickAction[] = [
  { id: 1, title: "إدارة المستخدمين", description: "إضافة المستخدمين وتعديل بياناتهم", path: "/users", icon: UserCog },
  { id: 2, title: "إدارة الأدوار", description: "إدارة الأدوار والصلاحيات", path: "/roles", icon: ShieldCheck },
  { id: 3, title: "إدارة الشركات", description: "إضافة الشركات وتحديث بياناتها", path: "/companies", icon: Building2 },
  { id: 4, title: "إدارة الفروع", description: "إضافة الفروع وربطها بالشركات", path: "/branches", icon: GitBranch },
  { id: 5, title: "التقارير", description: "عرض التقارير المالية والتشغيلية", path: "/reports", icon: BarChart3 },
  { id: 6, title: "المستندات", description: "متابعة المستندات والعمليات", path: "/accounting", icon: FileText },
];