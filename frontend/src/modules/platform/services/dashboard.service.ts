import client from "@/shared/api/client";

export interface DashboardSummary {
  tenant: { id: number; name: string | null; slug: string | null } | null;
  users: { total: number; active: number };
  companies: { total: number; active: number };
  branches: { total: number; active: number };
  revenue_overview: { month: string; revenue: number; expenses: number }[];
  recent_activities: { id: number; title: string; description: string; time: string; status: "success" | "warning" | "info" | "danger" }[];
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await client.get<DashboardSummary>("/dashboard/summary");
  return response.data;
}