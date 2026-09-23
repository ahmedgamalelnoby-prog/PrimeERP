import { saasEntitlementsApi } from "../api/entitlements.api";

export const saasEntitlementsService = {
  listModules: saasEntitlementsApi.listModules,
  listPlanModules: saasEntitlementsApi.listPlanModules,
  setPlanModule: saasEntitlementsApi.setPlanModule,
  getPlanLimits: saasEntitlementsApi.getPlanLimits,
  updatePlanLimits: saasEntitlementsApi.updatePlanLimits,
};
