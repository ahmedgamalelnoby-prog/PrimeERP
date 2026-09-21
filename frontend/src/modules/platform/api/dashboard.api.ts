import client from "@/shared/api/client";

export interface DashboardSummary {
  companies: number;
  branches: number;
  users: number;
  customers: number;
  revenue_current_month: number;
  revenue_previous_month: number;
}

export const dashboardApi = {
  summary() {
    return client.get<DashboardSummary>("/platform/dashboard/summary").then((response) => response.data);
  },
};
