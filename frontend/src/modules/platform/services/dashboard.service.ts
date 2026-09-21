import client from "@/shared/api/client";

export interface DashboardSummary {
  tenant: { id: number; name: string | null; slug: string | null } | null;
  users: { total: number; active: number };
  companies: { total: number; active: number };
  branches: { total: number; active: number };
}

export async function getDashboardSummary(): Promise<DashboardSummary> {
  const response = await client.get<DashboardSummary>("/dashboard/summary");
  return response.data;
}