import client from "@/shared/api/client";
import type { Plan } from "./plans.types";

export const plansApi = {
  async list() {
    const response = await client.get<Plan[]>("/plans/");
    return response.data;
  },
  async get(id: number) {
    const response = await client.get<Plan>(`/plans/${id}`);
    return response.data;
  },
};