import client from "@/shared/api/client";

export type Document = {
  id: number;
  company_id: number;
  partner_id: number;
  document_type: string;
  source_order_id?: number | null;
  number: string;
  document_date: string;
  status: string;
  warehouse_id: number | null;
  subtotal: string | number;
  tax_total: string | number;
  discount_total: string | number;
  paid_total: string | number;
  total: string | number;
};

export type Partner = {
  id: number;
  company_id: number;
  partner_type: string;
  name: string;
  code?: string | null;
};

export type DocumentLine = {
  item_id: number;
  source_sales_line_id?: number;
  source_purchase_line_id?: number;
  variant_id?: number;
  tax_rate_id?: number;
  description?: string;
  quantity: number;
  unit_price: number;
  discount_percent?: number;
  tax_percent?: number;
};

export type DocumentCreate = {
  company_id: number;
  partner_id: number;
  document_type: string;
  source_order_id?: number;
  receipt_ids?: number[];
  number: string;
  document_date: string;
  warehouse_id?: number;
  notes?: string;
  lines: DocumentLine[];
};

export type PaymentCreate = {
  company_id: number;
  document_id: number;
  payment_date: string;
  amount: number;
  method: string;
  reference?: string;
  idempotency_key?: string;
  notes?: string;
  wht_amount?: number;
  auto_wht?: boolean;
  cheque_number?: string;
  cheque_bank_name?: string;
  cheque_account_number?: string;
  cheque_due_date?: string;
};

const company = () => {
  const id = Number(localStorage.getItem("company_id"));
  if (!Number.isInteger(id) || id <= 0) throw new Error("اختر شركة فعالة أولاً.");
  return id;
};

const today = () => new Date().toISOString().slice(0, 10);
const newPaymentIdempotencyKey = () => crypto.randomUUID();

export const salesApi = {
  list: () => client.get<Document[]>("/commerce/sales/documents", { params: { company_id: company() } }).then(r => r.data),
  partners: () => client.get<Partner[]>("/commerce/partners", { params: { company_id: company(), partner_type: "customer" } }).then(r => r.data),
  create: (payload: Omit<DocumentCreate, "company_id">) => client.post<Document>("/commerce/sales/documents", { ...payload, company_id: company() }).then(r => r.data),
  confirm: (id: number) => client.post<Document>(`/commerce/sales/${id}/confirm`, null, { params: { company_id: company() } }).then(r => r.data),
  decideApproval: (id: number, decision: "approve" | "reject") => client.post<Document>(`/commerce/sales/${id}/approval-decision`, { decision }, { params: { company_id: company() } }).then(r => r.data),
  postInventory: (id: number) => client.post<Document>(`/commerce/sales/${id}/post-inventory`, null, { params: { company_id: company() } }).then(r => r.data),
  pay: (id: number, amount: number, method: string, idempotencyKey = newPaymentIdempotencyKey()) => client.post<Document>(`/commerce/sales/${id}/payments`, { company_id: company(), document_id: id, payment_date: today(), amount, method, auto_wht: true, idempotency_key: idempotencyKey }).then(r => r.data),
  payments: (id?: number) => client.get("/commerce/payments", { params: { company_id: company(), document_kind: "sale", ...(id ? { document_id: id } : {}) } }).then(r => r.data),
  reversePayment: (paymentId: number) => client.post<Document>(`/commerce/payments/${paymentId}/reverse`, { company_id: company(), reversal_date: today() }).then(r => r.data),
};

export const purchasingApi = {
  list: () => client.get<Document[]>("/commerce/purchases/documents", { params: { company_id: company() } }).then(r => r.data),
  partners: () => client.get<Partner[]>("/commerce/partners", { params: { company_id: company(), partner_type: "vendor" } }).then(r => r.data),
  create: (payload: Omit<DocumentCreate, "company_id">) => client.post<Document>("/commerce/purchases/documents", { ...payload, company_id: company() }).then(r => r.data),
  confirm: (id: number) => client.post<Document>(`/commerce/purchases/${id}/confirm`, null, { params: { company_id: company() } }).then(r => r.data),
  decideApproval: (id: number, decision: "approve" | "reject") => client.post<Document>(`/commerce/purchases/${id}/approval-decision`, { decision }, { params: { company_id: company() } }).then(r => r.data),
  receive: (id: number) => client.post<Document>(`/commerce/purchases/${id}/receive`, null, { params: { company_id: company() } }).then(r => r.data),
  pay: (id: number, amount: number, method: string, idempotencyKey = newPaymentIdempotencyKey()) => client.post<Document>(`/commerce/purchases/${id}/payments`, { company_id: company(), document_id: id, payment_date: today(), amount, method, auto_wht: true, idempotency_key: idempotencyKey }).then(r => r.data),
  payments: (id?: number) => client.get("/commerce/payments", { params: { company_id: company(), document_kind: "purchase", ...(id ? { document_id: id } : {}) } }).then(r => r.data),
  reversePayment: (paymentId: number) => client.post<Document>(`/commerce/payments/${paymentId}/reverse`, { company_id: company(), reversal_date: today() }).then(r => r.data),
};