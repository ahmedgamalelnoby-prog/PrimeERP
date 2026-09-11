export type PlanStatus = "draft" | "active" | "inactive" | "archived";
export type PlanType = "free" | "standard" | "professional" | "enterprise" | "custom";
export type BillingCycle = "monthly" | "quarterly" | "semi_annual" | "yearly";
export type PlanCurrency = "EGP" | "USD" | "EUR" | "SAR" | "AED";

export interface Plan {
  id: number;
  code: string;
  version: number;
  name: string;
  name_ar?: string | null;
  display_name?: string | null;
  description?: string | null;
  monthly_price: number;
  yearly_price: number;
  currency: PlanCurrency;
  billing_cycle: BillingCycle;
  trial_days: number;
  grace_period_days: number;
  effective_from?: string | null;
  effective_to?: string | null;
  is_default: boolean;
  is_public: boolean;
  is_free: boolean;
  is_custom: boolean;
  status: PlanStatus;
  plan_type: PlanType;
  sort_order: number;
}
