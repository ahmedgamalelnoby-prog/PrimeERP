import client from "@/shared/api/client";

const company=()=>{const n=Number(localStorage.getItem("company_id"));if(!Number.isInteger(n)||n<=0)throw new Error("اختر شركة فعالة أولاً.");return n};

export type AgingRow={direction:string;document_id:number;document_number:string;partner_id:number;document_date:string;due_date:string;total:string|number;paid_total:string|number;outstanding:string|number;days_overdue:number;bucket:string};
export type AgingSummary={as_of:string;receivable:string|number;payable:string|number;net:string|number;rows:AgingRow[]};

export const arApApi={aging:(asOf?:string)=>client.get<AgingSummary>("/commerce/ar-ap/aging",{params:{company_id:company(),...(asOf?{as_of:asOf}:{})}})};

export type ARAllocation={document_id:number;amount:number};
export const arApi={
  unapplied:(paymentId:number)=>client.get("/ar/payments/"+paymentId+"/unapplied",{params:{company_id:company()}}),
  allocate:(paymentId:number,allocations:ARAllocation[])=>client.post("/ar/payments/"+paymentId+"/allocate",{company_id:company(),payment_id:paymentId,allocations}),
  autoMatch:(paymentId:number,partnerId:number,asOf?:string)=>client.post("/ar/payments/"+paymentId+"/auto-match",{company_id:company(),partner_id:partnerId,payment_id:paymentId,as_of:asOf}),
  reconcile:(partnerId?:number,asOf?:string)=>client.post("/ar/reconcile",{company_id:company(),partner_id:partnerId,as_of:asOf,persist:true}),
  credit:(partnerId:number)=>client.get("/ar/credit/"+partnerId,{params:{company_id:company()}}),
  writeOffs:(status?:string)=>client.get("/ar/write-offs",{params:{company_id:company(),...(status?{status}:{})}}),
};
