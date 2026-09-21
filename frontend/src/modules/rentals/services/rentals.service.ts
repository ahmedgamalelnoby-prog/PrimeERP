import client from "@/shared/api/client";
import type {RentalCharge,RentalContract,PricingType} from "../types/rentals";
export const rentalsService={
 contracts:()=>client.get<RentalContract[]>("/rentals/contracts").then(r=>r.data),
 charges:()=>client.get<RentalCharge[]>("/rentals/charges").then(r=>r.data),
 activate:(id:number)=>client.post<RentalContract>("/rentals/contracts/"+id+"/activate").then(r=>r.data),
 terminate:(id:number)=>client.post<RentalContract>("/rentals/contracts/"+id+"/terminate").then(r=>r.data),
 charge:(payload:{contract_id:number;charge_date:string;period_start:string;period_end:string;revenue_amount:number})=>client.post<RentalCharge>("/rentals/charges",payload).then(r=>r.data),
 createContract:(payload:{number:string;unit_id:number;rental_tenant_id:number;branch_id?:number;start_date:string;end_date:string;pricing_type:PricingType;fixed_rent:number;minimum_guarantee:number;revenue_share_percent:number;maintenance_amount:number;security_deposit:number;vat_percent:number;wht_percent:number;notes?:string})=>client.post<RentalContract>("/rentals/contracts",payload).then(r=>r.data)
};
