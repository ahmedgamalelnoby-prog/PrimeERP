import { plansApi } from "./plans.api";
import type { Plan } from "./plans.types";

export const plansService = {
  async list(): Promise<Plan[]> {
    return plansApi.list();
  },
  async get(id: number): Promise<Plan> {
    return plansApi.get(id);
  },
};
