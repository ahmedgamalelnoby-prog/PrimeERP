import apiClient from "@/shared/api/client";

import type { Role } from "../types/role";

export const rolesService = {
  async getAll(): Promise<Role[]> {
    const response = await apiClient.get<Role[]>(
      "/roles/",
    );

    return response.data;
  },
};
