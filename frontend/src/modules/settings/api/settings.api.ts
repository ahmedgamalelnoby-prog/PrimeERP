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


export interface CompanyLegalTaxProfile {
  id: number;
  tenant_id: number;
  name: string;
  legal_name: string | null;
  tax_id: string | null;
  commercial_registration_number: string | null;
  tax_authority: string | null;
  eta_registration_status: string;
  eta_taxpayer_id: string | null;
  eta_last_verified_at: string | null;
  address: string | null;
}
export type CompanyLegalTaxUpdate = Partial<Pick<CompanyLegalTaxProfile, "name" | "legal_name" | "tax_id" | "commercial_registration_number" | "tax_authority">>;
export const companyLegalTaxApi = {
  async list() {
    const response = await client.get<CompanyLegalTaxProfile[]>("/companies?active_only=true");
    return response.data;
  },
  async update(companyId: number, payload: CompanyLegalTaxUpdate) {
    const response = await client.patch<CompanyLegalTaxProfile>(`/companies/${companyId}`, payload);
    return response.data;
  },
};
