import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import toast from "react-hot-toast";
import client from "@/shared/api/client";
import { notificationsService } from "../services/notifications.service";
import type { NotificationChannel, NotificationCompany, NotificationDelivery, NotificationGroup, NotificationInboxItem, NotificationTemplate } from "../types/notifications";

const card = "rounded-2xl border border-border bg-card p-5 shadow-sm";
const field = "w-full rounded-lg border border-input bg-background px-3 py-2 text-sm";
const label = "mb-1 block text-sm font-semibold text-foreground";

export default function NotificationsPage() {
  const [companies, setCompanies] = useState<NotificationCompany[]>([]);
  const [companyId, setCompanyId] = useState(Number(localStorage.getItem("company_id")) || 0);
  const [inbox, setInbox] = useState<NotificationInboxItem[]>([]);
  const [groups, setGroups] = useState<NotificationGroup[]>([]);
  const [templates, setTemplates] = useState<NotificationTemplate[]>([]);
  const [deliveries, setDeliveries] = useState<NotificationDelivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sendForm, setSendForm] = useState({ channel: "email" as NotificationChannel, destination: "", group_id: "", template_code: "", title: "", body: "" });
  const [groupForm, setGroupForm] = useState({ code: "", name: "", channel: "email" as "email" | "whatsapp", members: "" });
  const [templateForm, setTemplateForm] = useState({ code: "", channel: "email" as NotificationChannel, title_template: "", body_template: "" });

  async function refresh(company: number) {
    if (!company) return;
    setLoading(true);
    try {
      const [messages, groupRows, templateRows, deliveryRows] = await Promise.all([
        notificationsService.inbox(company), notificationsService.groups(company),
        notificationsService.templates(company), notificationsService.deliveries(company),
      ]);
      setInbox(messages); setGroups(groupRows); setTemplates(templateRows); setDeliveries(deliveryRows);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? "تعذر تحميل مركز الرسائل");
    } finally { setLoading(false); }
  }

  useEffect(() => {
    client.get<NotificationCompany[]>("/companies?active_only=true").then(({ data }) => {
      setCompanies(data);
      const saved = Number(localStorage.getItem("company_id")) || companyId;
      const selected = data.some((company) => company.id === saved) ? saved : (data[0]?.id ?? 0);
      setCompanyId(selected);
      if (selected) localStorage.setItem("company_id", String(selected));
    }).catch((error: any) => {
      toast.error(error?.response?.data?.detail ?? "تعذر تحميل الشركات");
      setLoading(false);
    });
  }, []);

  useEffect(() => { void refresh(companyId); }, [companyId]);

  async function submitSend(event: FormEvent) {
    event.preventDefault();
    if (!companyId) return;
    try {
      setSaving(true);
      const payload: any = {
        company_id: companyId, channel: sendForm.channel, title: sendForm.title,
        body: sendForm.body, idempotency_key: crypto.randomUUID(),
      };
      if (sendForm.template_code) payload.template_code = sendForm.template_code;
      if (sendForm.channel !== "in_app") {
        if (sendForm.group_id) payload.group_id = Number(sendForm.group_id);
        else payload.destination = sendForm.destination.trim();
      }
      const result = await notificationsService.send(payload);
      toast.success(`تم الإرسال: ${result.sent_count} ناجح، ${result.failed_count} فشل`);
      setSendForm((old) => ({ ...old, destination: "", title: "", body: "" }));
      await refresh(companyId);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? "تعذر إرسال الرسالة");
    } finally { setSaving(false); }
  }

  async function submitGroup(event: FormEvent) {
    event.preventDefault();
    const members = groupForm.members.split(/\r?\n/).map((destination) => destination.trim()).filter(Boolean).map((destination) => ({ destination, label: "" }));
    if (!companyId || !members.length) { toast.error("أضف مستلمًا واحدًا على الأقل"); return; }
    try {
      setSaving(true);
      await notificationsService.saveGroup({ company_id: companyId, code: groupForm.code.trim(), name: groupForm.name.trim(), channel: groupForm.channel, members, is_active: true });
      toast.success("تم حفظ مجموعة المستلمين");
      setGroupForm({ code: "", name: "", channel: "email", members: "" });
      await refresh(companyId);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? "تعذر حفظ المجموعة");
    } finally { setSaving(false); }
  }

  async function submitTemplate(event: FormEvent) {
    event.preventDefault();
    if (!companyId) return;
    try {
      setSaving(true);
      await notificationsService.saveTemplate({ company_id: companyId, code: templateForm.code.trim(), channel: templateForm.channel, title_template: templateForm.title_template, body_template: templateForm.body_template, is_active: true });
      toast.success("تم حفظ قالب الرسالة");
      setTemplateForm({ code: "", channel: "email", title_template: "", body_template: "" });
      await refresh(companyId);
    } catch (error: any) {
      toast.error(error?.response?.data?.detail ?? "تعذر حفظ القالب");
    } finally { setSaving(false); }
  }

  async function markRead(id: number) {
    try { await notificationsService.markRead(companyId, id); await refresh(companyId); }
    catch (error: any) { toast.error(error?.response?.data?.detail ?? "تعذر تحديث الإشعار"); }
  }

  return <div className="mx-auto w-full max-w-[1500px] space-y-6 p-4 md:p-6" dir="rtl">
    <header className="rounded-3xl bg-gradient-to-l from-slate-950 via-blue-900 to-sky-600 p-7 text-white">
      <p className="text-sm text-blue-100">الإعدادات والتواصل</p>
      <h1 className="mt-2 text-3xl font-black">مركز الرسائل والإشعارات</h1>
      <p className="mt-3 max-w-3xl text-sm leading-7 text-blue-50">إدارة قوالب البريد وواتساب، قوائم المستلمين، إرسال الرسائل، ومراجعة سجل التسليم والإشعارات الداخلية.</p>
      <div className="mt-5 max-w-md">
        <label className="mb-1 block text-sm font-semibold">الشركة</label>
        <select className="w-full rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-white" value={companyId || ""} onChange={(e) => { const id = Number(e.target.value); setCompanyId(id); localStorage.setItem("company_id", String(id)); }}>
          <option value="" className="text-black">اختر الشركة</option>
          {companies.map((company) => <option key={company.id} value={company.id} className="text-black">{company.name}</option>)}
        </select>
      </div>
    </header>

    <div className="grid gap-5 xl:grid-cols-2">
      <section className={card}>
        <h2 className="text-lg font-bold">إرسال رسالة</h2>
        <form className="mt-4 space-y-3" onSubmit={submitSend}>
          <div><label className={label}>القناة</label><select className={field} value={sendForm.channel} onChange={(e) => setSendForm({ ...sendForm, channel: e.target.value as NotificationChannel, group_id: "" })}><option value="email">البريد الإلكتروني</option><option value="whatsapp">WhatsApp</option><option value="in_app">إشعار داخل النظام لنفسي</option></select></div>
          {sendForm.channel !== "in_app" && <div><label className={label}>مجموعة مستلمين (اختياري)</label><select className={field} value={sendForm.group_id} onChange={(e) => setSendForm({ ...sendForm, group_id: e.target.value, destination: "" })}><option value="">إرسال إلى مستلم واحد</option>{groups.filter((group) => group.channel === sendForm.channel && group.is_active).map((group) => <option key={group.id} value={group.id}>{group.name} ({group.members.length})</option>)}</select></div>}
          {sendForm.channel !== "in_app" && !sendForm.group_id && <div><label className={label}>المستلم</label><input className={field} required value={sendForm.destination} onChange={(e) => setSendForm({ ...sendForm, destination: e.target.value })} placeholder={sendForm.channel === "email" ? "name@example.com" : "+201xxxxxxxxx"} /></div>}
          <div><label className={label}>قالب جاهز (اختياري)</label><select className={field} value={sendForm.template_code} onChange={(e) => setSendForm({ ...sendForm, template_code: e.target.value })}><option value="">استخدم النص المكتوب أدناه</option>{templates.filter((template) => template.channel === sendForm.channel && template.is_active).map((template) => <option key={template.id} value={template.code}>{template.code}</option>)}</select></div>
          <div><label className={label}>العنوان</label><input className={field} value={sendForm.title} onChange={(e) => setSendForm({ ...sendForm, title: e.target.value })} maxLength={255} /></div>
          <div><label className={label}>نص الرسالة</label><textarea className={field} rows={4} value={sendForm.body} onChange={(e) => setSendForm({ ...sendForm, body: e.target.value })} placeholder="يمكن استخدام قالب محفوظ أو كتابة رسالة مباشرة." /></div>
          <button disabled={saving || !companyId} className="rounded-lg bg-primary px-4 py-2 text-sm font-bold text-primary-foreground disabled:opacity-50">{saving ? "جارٍ التنفيذ..." : "إرسال وتسجيل النتيجة"}</button>
        </form>
        <p className="mt-3 text-xs leading-6 text-muted-foreground">مجموعات واتساب هنا هي قوائم توزيع داخل النظام؛ تُرسل رسالة منفصلة لكل رقم عضو، وليست رسالة إلى مجموعة واتساب فعلية.</p>
      </section>

      <section className={card}>
        <h2 className="text-lg font-bold">إنشاء مجموعة مستلمين</h2>
        <form className="mt-4 space-y-3" onSubmit={submitGroup}>
          <div className="grid gap-3 sm:grid-cols-2"><div><label className={label}>كود المجموعة</label><input className={field} required pattern="[A-Za-z0-9_.-]+" value={groupForm.code} onChange={(e) => setGroupForm({ ...groupForm, code: e.target.value })} /></div><div><label className={label}>اسم المجموعة</label><input className={field} required value={groupForm.name} onChange={(e) => setGroupForm({ ...groupForm, name: e.target.value })} /></div></div>
          <div><label className={label}>القناة</label><select className={field} value={groupForm.channel} onChange={(e) => setGroupForm({ ...groupForm, channel: e.target.value as "email" | "whatsapp" })}><option value="email">بريد إلكتروني</option><option value="whatsapp">WhatsApp</option></select></div>
          <div><label className={label}>المستلمون (كل عنوان أو رقم في سطر)</label><textarea className={field} rows={5} required value={groupForm.members} onChange={(e) => setGroupForm({ ...groupForm, members: e.target.value })} placeholder={"finance@example.com\naccounts@example.com"} /></div>
          <button disabled={saving || !companyId} className="rounded-lg border border-border px-4 py-2 text-sm font-bold disabled:opacity-50">حفظ المجموعة</button>
        </form>
        <div className="mt-5 space-y-2">{groups.map((group) => <div key={group.id} className="flex items-center justify-between rounded-lg bg-muted/50 px-3 py-2 text-sm"><span className="font-semibold">{group.name}</span><span className="text-muted-foreground">{group.channel} · {group.members.length} مستلم</span></div>)}</div>
      </section>

      <section className={card}>
        <h2 className="text-lg font-bold">قوالب الرسائل</h2>
        <form className="mt-4 space-y-3" onSubmit={submitTemplate}>
          <div className="grid gap-3 sm:grid-cols-2"><div><label className={label}>كود القالب</label><input className={field} required pattern="[A-Za-z0-9_.-]+" value={templateForm.code} onChange={(e) => setTemplateForm({ ...templateForm, code: e.target.value })} /></div><div><label className={label}>القناة</label><select className={field} value={templateForm.channel} onChange={(e) => setTemplateForm({ ...templateForm, channel: e.target.value as NotificationChannel })}><option value="email">البريد الإلكتروني</option><option value="whatsapp">WhatsApp</option><option value="in_app">إشعار داخلي</option></select></div></div>
          <div><label className={label}>عنوان القالب</label><input className={field} value={templateForm.title_template} onChange={(e) => setTemplateForm({ ...templateForm, title_template: e.target.value })} /></div>
          <div><label className={label}>نص القالب</label><textarea className={field} rows={4} required value={templateForm.body_template} onChange={(e) => setTemplateForm({ ...templateForm, body_template: e.target.value })} placeholder="مرحبًا {{ customer_name }}، رقم الفاتورة {{ invoice_no }}" /></div>
          <button disabled={saving || !companyId} className="rounded-lg border border-border px-4 py-2 text-sm font-bold disabled:opacity-50">حفظ القالب</button>
        </form>
        <div className="mt-5 space-y-2">{templates.map((template) => <div key={template.id} className="rounded-lg bg-muted/50 px-3 py-2 text-sm"><span className="font-semibold">{template.code}</span><span className="mr-2 text-muted-foreground">{template.channel}</span></div>)}</div>
      </section>

      <section className={card}>
        <div className="flex items-center justify-between"><h2 className="text-lg font-bold">الإشعارات الداخلية</h2><span className="text-xs text-muted-foreground">{inbox.filter((item) => !item.read_at).length} غير مقروء</span></div>
        <div className="mt-4 space-y-3">{loading ? <p className="text-sm text-muted-foreground">جارٍ التحميل...</p> : inbox.length ? inbox.map((item) => <article key={item.id} className="rounded-xl border border-border p-3"><div className="flex items-start justify-between gap-3"><div><h3 className="font-bold">{item.title || "إشعار"}</h3><p className="mt-1 whitespace-pre-wrap text-sm leading-6">{item.body}</p><p className="mt-2 text-xs text-muted-foreground">{new Date(item.created_at).toLocaleString()}</p></div>{!item.read_at && <button className="shrink-0 text-xs font-bold text-primary" onClick={() => void markRead(item.id)}>تمت القراءة</button>}</div></article>) : <p className="text-sm text-muted-foreground">لا توجد إشعارات داخلية حتى الآن.</p>}</div>
      </section>
    </div>

    <section className={card}>
      <h2 className="text-lg font-bold">سجل الإرسال</h2>
      <div className="mt-4 overflow-x-auto"><table className="w-full min-w-[720px] text-right text-sm"><thead><tr className="border-b border-border text-muted-foreground"><th className="p-2">القناة</th><th className="p-2">المستلم</th><th className="p-2">الحالة</th><th className="p-2">مرجع المزود</th><th className="p-2">الخطأ</th><th className="p-2">التاريخ</th></tr></thead><tbody>{deliveries.map((delivery) => <tr key={delivery.id} className="border-b border-border/60"><td className="p-2">{delivery.channel}</td><td className="p-2">{delivery.destination}</td><td className="p-2">{delivery.status}</td><td className="p-2">{delivery.provider_reference || "—"}</td><td className="p-2">{delivery.error_code || "—"}</td><td className="p-2">{new Date(delivery.created_at).toLocaleString()}</td></tr>)}{!deliveries.length && <tr><td colSpan={6} className="p-4 text-center text-muted-foreground">لا توجد عمليات إرسال مسجلة.</td></tr>}</tbody></table></div>
    </section>
  </div>;
}
