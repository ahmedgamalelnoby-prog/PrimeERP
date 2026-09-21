export type PaymentMethod = "cash" | "card" | "bank" | "other";

export interface POSOutlet { id:number; company_id:number; branch_id:number; inventory_location_id:number; code:string; name:string; is_active:boolean; }
export interface POSDevice { id:number; company_id:number; outlet_id:number; code:string; name:string; is_active:boolean; }
export interface POSSession { id:number; company_id:number; outlet_id:number; device_id:number; cashier_user_id:number; status:string; closing_total:number|null; closing_cash:number|null; closing_card:number|null; closing_bank:number|null; closing_other:number|null; }
export interface POSOrder { id:number; company_id:number; session_id:number; number:string; status:string; subtotal:number; tax_total:number; total:number; paid_total:number; }
export interface POSPayment { id:number; company_id:number; order_id:number; method:PaymentMethod; amount:number; idempotency_key:string; status:string; accounting_entry_id:number|null; }

export interface CreateOutlet { company_id:number; branch_id:number; inventory_location_id:number; code:string; name:string; }
export interface CreateDevice { company_id:number; outlet_id:number; code:string; name:string; }
export interface OpenSession { company_id:number; outlet_id:number; device_id:number; cashier_user_id:number; }
export interface OrderLine { item_id:number; variant_id:number|null; quantity:number; unit_price:number; tax_percent:number; }
export interface CreateOrder { company_id:number; session_id:number; number:string; lines:OrderLine[]; }
export interface CreatePayment { company_id:number; order_id:number; method:PaymentMethod; amount:number; idempotency_key:string; }
export interface CloseSession { company_id:number; closing_total:number; closing_cash?:number; closing_card?:number; closing_bank?:number; closing_other?:number; }
