export type NotificationChannel = "email" | "whatsapp" | "in_app";

export interface NotificationCompany { id: number; name: string; }
export interface NotificationInboxItem {
  id: number; title: string; body: string; status: string;
  created_at: string; sent_at: string | null; read_at: string | null;
}
export interface NotificationGroupMember { destination: string; label: string; is_active: boolean; }
export interface NotificationGroup {
  id: number; code: string; name: string; channel: "email" | "whatsapp";
  is_active: boolean; members: NotificationGroupMember[];
}
export interface NotificationTemplate {
  id: number; code: string; channel: NotificationChannel; title_template: string;
  body_template: string; is_active: boolean;
}
export interface NotificationDelivery {
  id: number; channel: NotificationChannel; destination: string; title: string;
  status: string; provider_reference: string | null; error_code: string | null;
  created_at: string; sent_at: string | null;
}
export interface NotificationSendResult {
  status: string; count: number; sent_count: number; failed_count: number;
  deliveries: Array<{id:number;channel:NotificationChannel;destination:string;status:string;provider_reference?:string|null;error_code?:string|null}>;
}
