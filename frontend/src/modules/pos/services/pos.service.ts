import { request } from "@/shared/api/request";
import type { CreateDevice, CreateOrder, CreateOutlet, CreatePayment, OpenSession, CloseSession, POSDevice, POSOrder, POSOutlet, POSPayment, POSSession, PaymentMethod } from "../types/pos";

export const posApi = {
  createOutlet: (payload:CreateOutlet) => request.post<POSOutlet>("/pos/outlets", payload).then(r=>r.data),
  createDevice: (payload:CreateDevice) => request.post<POSDevice>("/pos/devices", payload).then(r=>r.data),
  openSession: (payload:OpenSession) => request.post<POSSession>("/pos/sessions/open", payload).then(r=>r.data),
  createOrder: (payload:CreateOrder) => request.post<POSOrder>("/pos/orders", payload).then(r=>r.data),
  finalizeOrder: (orderId:number, companyId:number) => request.post<POSOrder>(`/pos/orders/${orderId}/finalize`, undefined, { params:{ company_id:companyId } }).then(r=>r.data),
  pay: (payload:CreatePayment) => request.post<POSPayment>("/pos/payments", payload).then(r=>r.data),
  closeSession: (sessionId:number, payload:CloseSession) => request.post<POSSession>(`/pos/sessions/${sessionId}/close`, payload).then(r=>r.data),
  savePaymentMapping: (companyId:number, method:PaymentMethod, accountCombinationId:number) => request.put(`/pos/payment-account-mappings/${method}`, undefined, { params:{ company_id:companyId, account_combination_id:accountCombinationId } }).then(r=>r.data),
};
