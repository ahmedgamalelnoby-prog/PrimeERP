import client from "@/shared/api/client";

export type CompanyPolicySetting = {
  key:string; module:string; category:string; type:"bool"|"int"|"number"|"string"|"enum";
  default:any; value:any; label:string; choices:string[]|null; status:"runtime"|"catalog";
};
export type CompanyPolicySettingsResponse = {
  company_id:number; company_name:string; categories:string[]; settings:CompanyPolicySetting[];
};
export const companyPolicySettingsApi = {
  async get(companyId:number) {
    const {data}=await client.get<CompanyPolicySettingsResponse>("/company-settings",{params:{company_id:companyId}});
    return data;
  },
  async update(companyId:number, settings:Record<string,unknown>) {
    const {data}=await client.put("/company-settings",{settings},{params:{company_id:companyId}});
    return data as {company_id:number;updated_keys:string[];updated_count:number};
  },
};
