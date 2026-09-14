import { useEffect, useState } from "react";

const API_BASE = (import.meta.env.VITE_API_URL || "/api/v1").replace(/\/$/, "");

type Report = { key: string; name: string };
type Schedule = { id: number; name: string; report_key: string; frequency: string; channels: string[]; recipients: string[]; include_ai: boolean; is_active: boolean; next_run_at: string | null };

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { credentials: "include", headers: { "Content-Type": "application/json", ...(init?.headers || {}) }, ...init });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload?.detail || "Request failed");
  return payload;
}

export default function AIReportingPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [message, setMessage] = useState("");
  const [name, setName] = useState("Weekly Management Summary");
  const [reportKey, setReportKey] = useState("management_summary");
  const [frequency, setFrequency] = useState("weekly");
  const [channel, setChannel] = useState("email");
  const [recipients, setRecipients] = useState("");

  const load = async () => {
    try {
      const [catalog, scheduled] = await Promise.all([
        api<{ data: { reports: Report[] } }>("/ai-reporting/catalog"),
        api<{ data: { schedules: Schedule[] } }>("/ai-reporting/schedules"),
      ]);
      setReports(catalog.data.reports);
      setSchedules(scheduled.data.schedules);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Unable to load AI Reporting");
    }
  };

  useEffect(() => { void load(); }, []);

  const createSchedule = async () => {
    try {
      await api("/ai-reporting/schedules", {
        method: "POST",
        body: JSON.stringify({ name, report_key: reportKey, frequency, channels: [channel], recipients: recipients.split(",").map((item) => item.trim()).filter(Boolean), include_ai: true }),
      });
      setMessage("تم إنشاء الجدول بنجاح");
      setRecipients("");
      await load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "تعذر إنشاء الجدول");
    }
  };

  return (
    <div className="space-y-6 p-6" dir="rtl">
      <div>
        <h1 className="text-3xl font-bold">التحليل الذكي والتقارير الآلية</h1>
        <p className="mt-2 text-sm text-muted-foreground">تحليل أداء الإدارة بالذكاء الاصطناعي وإرسال التقارير تلقائيًا عبر البريد أو WhatsApp.</p>
      </div>

      {message && <div className="rounded-xl border bg-card p-3 text-sm">{message}</div>}

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">التقارير المتاحة</div><div className="mt-2 text-3xl font-bold">{reports.length}</div></div>
        <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">الجداول النشطة</div><div className="mt-2 text-3xl font-bold">{schedules.filter((item) => item.is_active).length}</div></div>
        <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">AI Model</div><div className="mt-2 text-lg font-semibold">GPT-5.6 Luna</div></div>
      </section>

      <section className="rounded-2xl border bg-card p-6">
        <h2 className="text-xl font-semibold">جدولة تقرير جديد</h2>
        <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <input className="rounded-lg border bg-background p-3" value={name} onChange={(e) => setName(e.target.value)} placeholder="اسم الجدول" />
          <select className="rounded-lg border bg-background p-3" value={reportKey} onChange={(e) => setReportKey(e.target.value)}>{reports.map((report) => <option key={report.key} value={report.key}>{report.name}</option>)}</select>
          <select className="rounded-lg border bg-background p-3" value={frequency} onChange={(e) => setFrequency(e.target.value)}><option value="daily">يومي</option><option value="weekly">أسبوعي</option><option value="monthly">شهري</option><option value="quarterly">ربع سنوي</option></select>
          <select className="rounded-lg border bg-background p-3" value={channel} onChange={(e) => setChannel(e.target.value)}><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select>
          <input className="rounded-lg border bg-background p-3 lg:col-span-2" value={recipients} onChange={(e) => setRecipients(e.target.value)} placeholder="المستلمين — افصل بينهم بفاصلة" />
        </div>
        <button className="mt-4 rounded-lg bg-primary px-5 py-3 font-semibold text-primary-foreground" onClick={() => void createSchedule()}>حفظ الجدولة</button>
      </section>

      <section className="rounded-2xl border bg-card p-6">
        <h2 className="text-xl font-semibold">الجداول الحالية</h2>
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm"><thead><tr className="border-b text-right"><th className="p-3">الاسم</th><th className="p-3">التقرير</th><th className="p-3">التكرار</th><th className="p-3">القنوات</th><th className="p-3">الحالة</th></tr></thead>
            <tbody>{schedules.map((item) => <tr className="border-b last:border-0" key={item.id}><td className="p-3">{item.name}</td><td className="p-3">{reports.find((report) => report.key === item.report_key)?.name || item.report_key}</td><td className="p-3">{item.frequency}</td><td className="p-3">{item.channels.join(" + ")}</td><td className="p-3">{item.is_active ? "نشط" : "متوقف"}</td></tr>)}</tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
