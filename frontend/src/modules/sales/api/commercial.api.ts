import client from "@/shared/api/client";

export type Document = { id:number; company_id:number; document_type:string; status:string; document_number?:string|null; partner_id?:number|null; total_amount:string|number; currency?:string|null; created_at?:string|null };
export type Partner = { id:number; company_id:number; partner_type:string; name:string; code?:string|null };

const company = () => {
 const id=Number(localStorage.getItem("company_id"));
 if(!Number.isInteger(id)||id<=0) throw new Error("اختر شركة فعالة أولاً.");
 return id;
};
export const salesApi = {
 list:()=>client.get<Document[]>("/commerce/sales/documents",{params:{company_id:company()}}).then(r=>r.data),
 partners:()=>client.get<Partner[]>("/commerce/partners",{params:{company_id:company(),partner_type:"customer"}}).then(r=>r.data),
 confirm:(id:number)=>client.post<Document>(`/commerce/sales/${id}/confirm`,null,{params:{company_id:company()}}).then(r=>r.data),
 postInventory:(id:number)=>client.post<Document>(`/commerce/sales/${id}/post-inventory`,null,{params:{company_id:company()}}).then(r=>r.data),
 payments:(id:number)=>client.get<Document[]>("/commerce/payments",{params:{company_id:company(),document_kind:"sale",document_id:id}}).then(r=>r.data),
};
export const purchasingApi = {
 list:()=>client.get<Document[]>("/commerce/purchases/documents",{params:{company_id:company()}}).then(r=>r.data),
 partners:()=>client.get<Partner[]>("/commerce/partners",{params:{company_id:company(),partner_type:"supplier"}}).then(r=>r.data),
 confirm:(id:number)=>client.post<Document>(`/commerce/purchases/${id}/confirm`,null,{params:{company_id:company()}}).then(r=>r.data),
 receive:(id:number)=>client.post<Document>(`/commerce/purchases/${id}/receive`,null,{params:{company_id:company()}}).then(r=>r.data),
 payments:(id:number)=>client.get<Document[]>("/commerce/payments",{params:{company_id:company(),document_kind:"purchase",document_id:id}}).then(r=>r.data),
};
