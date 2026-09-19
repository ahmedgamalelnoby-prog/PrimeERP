import client from "@/shared/api/client";

const company=()=>{const n=Number(localStorage.getItem("company_id"));if(!Number.isInteger(n)||n<=0)throw new Error("اختر شركة فعالة أولاً.");return n};
export type StatementRow={date:string;document_type:string;document_id:number|null;reference:string;debit:string|number;credit:string|number;balance:string|number};
export type PartnerStatement={company_id:number;partner_id:number;direction:"customer"|"vendor";from_date:string|null;to_date:string|null;as_of:string;opening_balance:string|number;closing_balance:string|number;rows:StatementRow[]};
export const partnerStatementApi={get:(partnerId:number,direction:"customer"|"vendor",fromDate?:string,toDate?:string,asOf?:string)=>client.get<PartnerStatement>("/commerce/partners/"+partnerId+"/statement",{params:{company_id:company(),direction,...(fromDate?{from_date:fromDate}:{}),...(toDate?{to_date:toDate}:{}),...(asOf?{as_of:asOf}:{})}})};
