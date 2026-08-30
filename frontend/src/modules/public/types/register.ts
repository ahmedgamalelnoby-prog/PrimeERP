import client from "@/shared/api/client";

export interface RegisterRequest {
  business_name: string;
  owner_name: string;
  username: string;
  email: string;
  phone?: string;
  password: string;
  business_type?: string;
  country_code?: string;
  language?: "ar" | "en";
  company_name?: string;
  branch_name?: string;
}

export interface RegisterResponse {
  [key: string]: unknown;
}

export async function register(
  payload: RegisterRequest,
): Promise<RegisterResponse> {
  const requestPayload = {
    business_name: payload.business_name.trim(),
    business_type: payload.business_type ?? "other",
    owner_name: payload.owner_name.trim(),
    username: payload.username.trim().toLowerCase(),
    email: payload.email.trim().toLowerCase(),
    phone: payload.phone?.trim() || null,
    password: payload.password,
    country_code: payload.country_code ?? "EG",
    language: payload.language ?? "ar",
    company_name: payload.company_name?.trim() || payload.business_name.trim(),
    branch_name: payload.branch_name?.trim() || "الفرع الرئيسي",
  };

  const response = await client.post<RegisterResponse>(
    "/saas/register",
    requestPayload,
  );

  return response.data;
}
