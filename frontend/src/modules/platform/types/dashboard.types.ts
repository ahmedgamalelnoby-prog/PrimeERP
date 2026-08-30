import type { LucideIcon } from "lucide-react";

export type ActivityStatus =
  | "success"
  | "warning"
  | "info"
  | "danger";

export interface DashboardStatistic {
  id: number;
  title: string;
  value: string;
  change: number;
  changeLabel: string;
  icon: LucideIcon;
}

export interface BusinessUnit {
  id: number;
  title: string;
  value: string | number;
  icon: LucideIcon;
}

export interface QuickAction {
  id: number;
  title: string;
  description: string;
  path: string;
  icon: LucideIcon;
}

export interface RecentActivity {
  id: number;
  title: string;
  description: string;
  time: string;
  status: ActivityStatus;
}

export interface RevenueOverviewPoint {
  month: string;
  revenue: number;
  expenses: number;
}