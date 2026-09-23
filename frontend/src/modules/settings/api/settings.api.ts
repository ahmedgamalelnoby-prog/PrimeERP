import client from "@/shared/api/client";

export interface TenantSettings {
  id: number;
  name: string;
  slug: string;
  business_type: string;
  phone: string | null;
  email: string;
  country_code: string;
  default_language: "ar" | "en";
  default_locale: string;
  timezone: string;
  currency_code: string;
  status: string;
  is_trial: boolean;
  trial_started_at: string | null;
  trial_ends_at: string | null;
}

export type TenantSettingsUpdate = Partial<Pick<
  TenantSettings,
  "name" | "phone" | "default_language" | "default_locale" | "timezone" | "currency_code" | "business_type"
>>;

export const settingsApi = {
  async get() {
    const response = await client.get<TenantSettings>("/saas/settings");
    return response.data;
  },
  async update(payload: TenantSettingsUpdate) {
    const response = await client.patch<TenantSettings>("/saas/settings", payload);
    return response.data;
  },
};
