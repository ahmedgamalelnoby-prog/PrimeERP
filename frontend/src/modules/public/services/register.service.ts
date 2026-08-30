import client from "@/shared/api/client";

import type {
  RegisterRequest,
  RegisterResponse,
} from "../types/register";

export async function registerCompany(
  payload: RegisterRequest,
): Promise<RegisterResponse> {
  const response = await client.post<RegisterResponse>(
    "/saas/register",
    payload,
  );

  return response.data;
}