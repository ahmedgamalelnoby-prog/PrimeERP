import client from "@/shared/api/client";

export type Category = { id:number; company_id:number; code:string; name_ar:string; name_en?:string|null; parent_id?:number|null; is_active:boolean };
export type PriceList = { id:number; company_id:number; code:string; name:string; currency:string; channel:string; is_default:boolean; is_active:boolean };
export type Recipe = { id:number; company_id:number; product_id:number; code:string; name_ar:string; name_en?:string|null; yield_quantity:string|number; waste_percentage:string|number; version:number; is_active:boolean; lines:Array<{id:number;line_no:number;ingredient_product_id:number;quantity:string|number;waste_percentage:string|number;uom_id?:number|null;notes?:string|null}>; total_cost:string|number; cost_per_yield:string|number };
export type PricingImpact = { target_margin:string|number; below_margin?:string|number; price_list_id?:number|null; quantity:string|number; count:number; items:Array<{product_id:number;product_name:string;price_list_id?:number|null;quantity:string|number;current_cost:string|number;sale_price:string|number;gross_margin_percentage:string|number;recommended_price_at_margin?:string|number|null;pricing_status:string;price_source:string}> };

export const productsApi = {
  categories(companyId:number) {
    return client.get<Category[]>("/catalog/categories",{params:{company_id:companyId}}).then(r=>r.data);
  },
  priceLists(companyId:number) {
    return client.get<PriceList[]>("/catalog/price-lists",{params:{company_id:companyId}}).then(r=>r.data);
  },
  recipes(companyId:number) {
    return client.get<Recipe[]>("/catalog/recipes",{params:{company_id:companyId}}).then(r=>r.data);
  },
  pricingImpact(companyId:number,targetMargin=30,belowMargin?:number) {
    return client.get<PricingImpact>("/catalog/pricing-impact",{params:{company_id:companyId,target_margin:targetMargin,below_margin:belowMargin}}).then(r=>r.data);
  },
};
