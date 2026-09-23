import client from "@/shared/api/client";

export interface Sasmodule {
  module_id: number;
  code: string;
  name_ar?: string | null;
  name_en?: string | null;
  is_core: boolean;
  is_enabled: boolean;
}

export const saasEntitlementsApi = {
  async listModules() {
    const response = await client.get<Sasmodule[]>("/platform/entitlements/modules");
    return response.data;
  },
  async listPlanModules(planId: number) {
    const response = await client.get<Sasmodule[]>(`/platform/entitlements/plans/${planId}/modules`);
    return response.data;
  },
  async setPlanModule(planId: number, moduleId: number, isEnabled: boolean) {
    const response = await client.put(
      `/platform/entitlements/plans/${planId}/modules/${moduleId}`,
      { is_enabled: isEnabled },
    );
    return response.data;
  },
  async getPlanLimits(planId: number) {
    const response = await client.get(`/platform/entitlements/plans/${planId}/limits`);
    return response.data;
  },
  async updatePlanLimits(planId: number, payload: Record<string, number | null>) {
    const response = await client.patch(`/platform/entitlements/plans/${planId}/limits`, payload);
    return response.data;
  },
};
