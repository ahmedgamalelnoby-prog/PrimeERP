import client from "@/shared/api/client";

export type StockMove={id:number;company_id:number;item_id:number;variant_id:number|null;source_location_id:number|null;destination_location_id:number|null;quantity:string|number;unit_cost:string|number;movement_type:string;transaction_date:string|null;reference:string|null;status:string;accounting_entry_id:number|null};
export type Transfer={id:number;company_id:number;source_warehouse_id:number;destination_warehouse_id:number;reference:string;status:string;notes:string|null};

const company=()=>{const id=Number(localStorage.getItem("company_id"));if(!Number.isInteger(id)||id<=0)throw new Error("اختر شركة فعالة أولاً.");return id;};

export const inventoryApi={
 listMoves:()=>client.get<StockMove[]>("/inventory/stock-moves",{params:{company_id:company()}}).then(r=>r.data),
 createMove:(payload:Omit<StockMove,"id"|"company_id"|"status"|"accounting_entry_id">)=>client.post<StockMove>("/inventory/stock-moves",{...payload,company_id:company()}).then(r=>r.data),
 postMove:(id:number)=>client.post<StockMove>(`/inventory/stock-moves/${id}/post`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 reverseMove:(id:number)=>client.post<StockMove>(`/inventory/stock-moves/${id}/reverse`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 listTransfers:()=>client.get<Transfer[]>("/inventory/transfers",{params:{company_id:company()}}).then(r=>r.data),
 createTransfer:(payload:Omit<Transfer,"id"|"company_id"|"status"> & {lines:Array<{item_id:number;source_location_id:number;destination_location_id:number;quantity:number|string;unit_cost:number|string}>})=>client.post<Transfer>("/inventory/transfers",{...payload,company_id:company()}).then(r=>r.data),
 requestTransfer:(id:number)=>client.post<Transfer>(`/inventory/transfers/${id}/request`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 approveTransfer:(id:number)=>client.post<Transfer>(`/inventory/transfers/${id}/approve`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 shipTransfer:(id:number)=>client.post<Transfer>(`/inventory/transfers/${id}/ship`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 receiveTransfer:(id:number)=>client.post<Transfer>(`/inventory/transfers/${id}/receive`,undefined,{params:{company_id:company()}}).then(r=>r.data),
 cancelTransfer:(id:number)=>client.post<Transfer>(`/inventory/transfers/${id}/cancel`,undefined,{params:{company_id:company()}}).then(r=>r.data),
};