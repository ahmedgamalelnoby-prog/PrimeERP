import client from "@/shared/api/client";

const company=()=>{const n=Number(localStorage.getItem("company_id"));if(!Number.isInteger(n)||n<=0)throw new Error("اختر شركة فعالة أولاً.");return n};

export type AgingRow={direction:string;document_id:number;document_number:string;partner_id:number;document_date:string;due_date:string;total:string|number;paid_total:string|number;outstanding:string|number;days_overdue:number;bucket:string};
export type AgingSummary={as_of:string;receivable:string|number;payable:string|number;net:string|number;rows:AgingRow[]};

export const arApApi={aging:(asOf?:string)=>client.get<AgingSummary>("/commerce/ar-ap/aging",{params:{company_id:company(),...(asOf?{as_of:asOf}:{})}})};
