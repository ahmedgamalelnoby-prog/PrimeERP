import client from "@/shared/api/client";
import type {
  NotificationChannel, NotificationDelivery, NotificationGroup, NotificationInboxItem,
  NotificationSendResult, NotificationTemplate,
} from "../types/notifications";

export const notificationsService = {
  async inbox(companyId: number) {
    const { data } = await client.get<NotificationInboxItem[]>("/notifications/inbox", { params: { company_id: companyId } });
    return data;
  },
  async markRead(companyId: number, id: number) {
    const { data } = await client.post("/notifications/" + id + "/read", null, { params: { company_id: companyId } });
    return data;
  },
  async groups(companyId: number) {
    const { data } = await client.get<NotificationGroup[]>("/notifications/groups", { params: { company_id: companyId } });
    return data;
  },
  async saveGroup(payload: { company_id:number; code:string; name:string; channel:"email"|"whatsapp"; members:Array<{destination:string;label:string}>; is_active:boolean }) {
    const { data } = await client.put("/notifications/groups", payload);
    return data;
  },
  async templates(companyId: number) {
    const { data } = await client.get<NotificationTemplate[]>("/notifications/templates", { params: { company_id: companyId } });
    return data;
  },
  async saveTemplate(payload: { company_id:number; code:string; channel:NotificationChannel; title_template:string; body_template:string; is_active:boolean }) {
    const { data } = await client.put("/notifications/templates", payload);
    return data;
  },
  async send(payload: { company_id:number; channel:NotificationChannel; destination?:string; group_id?:number; template_code?:string; title:string; body:string; idempotency_key?:string }) {
    const { data } = await client.post<NotificationSendResult>("/notifications/send", payload);
    return data;
  },
  async deliveries(companyId: number) {
    const { data } = await client.get<NotificationDelivery[]>("/notifications/deliveries", { params: { company_id: companyId } });
    return data;
  },
};
