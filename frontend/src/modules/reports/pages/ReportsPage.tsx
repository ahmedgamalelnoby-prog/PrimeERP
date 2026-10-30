import { FormEvent, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "@/shared/api/client";
import { formatCompanyDateTime, useCompanyDateFormat } from "@/utils/format-date";

type Schedule = { id:number; report_definition_id:number; channel:string; destination:string; schedule:string; format:string; is_active:boolean; last_status?:string|null; next_run_at?:string|null };

function getStoredCompanyId(): number {
  try {
    const value = Number(localStorage.getItem("company_id"));
    return Number.isInteger(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

export default function ReportsPage(){
  const {t,i18n}=useTranslation();
  const [question,setQuestion]=useState("");
  const [metrics,setMetrics]=useState('{"gross_margin_pct":20,"overdue_ratio_pct":10}');
  const [result,setResult]=useState("");
  const [error,setError]=useState("");
  const [loading,setLoading]=useState(false);
  const [deliveryLoading,setDeliveryLoading]=useState(false);
  const [channel,setChannel]=useState<"email"|"whatsapp">("email");
  const [destination,setDestination]=useState("");
  const [title,setTitle]=useState("PrimeERP Management Report");
  const [body,setBody]=useState("");
  const [schedule,setSchedule]=useState("daily:09:00");
  const [schedules,setSchedules]=useState<Schedule[]>([]);
  const [companyId,setCompanyId]=useState(getStoredCompanyId);
  const [fromDate,setFromDate]=useState("");
  const [toDate,setToDate]=useState("");
  const dateFormat = useCompanyDateFormat(companyId);

  useEffect(()=>{loadSchedules();},[companyId]);

  async function loadSchedules(){
    if(!companyId){setSchedules([]);return;}
    try{const r=await client.get("/reports/schedules",{params:{company_id:companyId}});setSchedules(r.data||[]);}
    catch(e:any){setError(e?.response?.data?.detail||t("reports.loadSchedulesFailed"));}
  }

  async function analyze(e:FormEvent){
    e.preventDefault();setLoading(true);setError("");
    try{
      const parsed=JSON.parse(metrics);
      if(!companyId){throw new Error("{t("reports.activeCompanyRequired")}");}
      if(fromDate&&toDate&&fromDate>toDate){throw new Error("{t("reports.invalidDateRange")}");}
      const r=await client.post("/reports/ai/analyze",{company_id:companyId,domain:"general",metrics:parsed,question:question||null,from_date:fromDate||null,to_date:toDate||null});
      setResult(JSON.stringify(r.data,null,2));
      setBody(JSON.stringify(r.data,null,2));
    }catch(e:any){setError(e?.message==="Unexpected end of JSON input"?"{t("reports.invalidMetricsJson")}":e?.response?.data?.detail||e?.message||t("reports.analyzeFailed"));}
    finally{setLoading(false);}
  }

  async function deliver(e:FormEvent){
    if(!companyId){setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");return;}
    e.preventDefault();setDeliveryLoading(true);setError("");
    try{
      await client.post("/reports/deliver",{company_id:companyId,channel,destination,title,body:body||result||"PrimeERP report"});
      setError(""); alert("{t("reports.deliverSuccess")}");
    }catch(e:any){setError(e?.response?.data?.detail||t("reports.deliverFailed"));}
    finally{setDeliveryLoading(false);}
  }

  async function createSchedule(e:FormEvent){
    if(!companyId){setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");return;}
    e.preventDefault();setDeliveryLoading(true);setError("");
    try{
      await client.post("/reports/schedules",{company_id:companyId,code:"management_snapshot",name:title,report_type:"snapshot",channel,destination,schedule,format:"text",parameters:{},filters:{}});
      await loadSchedules();
    }catch(e:any){setError(e?.response?.data?.detail||t("reports.createScheduleFailed"));}
    finally{setDeliveryLoading(false);}
  }

  return <section className="space-y-6 p-6" dir={i18n.dir()}>
    <header>
      <h1 className="text-2xl font-bold">{t("reports.title")}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t("reports.description")}</p>
    </header>

    {error&&<div className="rounded-lg bg-destructive/10 p-3 text-sm">{error}</div>}

    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={analyze} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <div><h2 className="font-semibold">{t("reports.smartAnalysis")}</h2><p className="text-xs text-muted-foreground">{t("reports.rulesWithoutAi")}</p></div>
        <label className="block text-sm font-semibold">{t("reports.analysisQuestion")}<textarea value={question} onChange={e=>setQuestion(e.target.value)} placeholder="{t("reports.analysisPlaceholder")}" className="mt-1 min-h-24 w-full rounded-lg border bg-background p-3"/></label>
        <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-semibold">{t("reports.fromDate")}<input type="date" value={fromDate} onChange={e=>setFromDate(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label><label className="text-sm font-semibold">{t("reports.toDate")}<input type="date" value={toDate} onChange={e=>setToDate(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label></div>
        <label className="block text-sm font-semibold">Metrics JSON<textarea value={metrics} onChange={e=>setMetrics(e.target.value)} className="mt-1 min-h-32 w-full rounded-lg border bg-background p-3 font-mono text-xs"/></label>
        <button disabled={loading} className="rounded-lg bg-primary px-5 py-2 text-primary-foreground">{loading?"{t("reports.analyzing")}":"{t("reports.analyze")}"}</button>
      </form>

      <form onSubmit={deliver} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <div><h2 className="font-semibold">{t("reports.deliverReport")}</h2><p className="text-xs text-muted-foreground">يتطلب إعداد SMTP أو WhatsApp في بيئة التشغيل.</p></div>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm font-semibold">{t("reports.company")}<input type="number" min="1" value={companyId} onChange={e=>setCompanyId(Number(e.target.value)||0)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
          <label className="text-sm font-semibold">{t("reports.channel")}<select value={channel} onChange={e=>setChannel(e.target.value as "email"|"whatsapp")} className="mt-1 w-full rounded-lg border bg-background p-2"><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select></label>
        </div>
        <label className="block text-sm font-semibold">{t("reports.destination")}<input value={destination} onChange={e=>setDestination(e.target.value)} placeholder={channel==="email"?"manager@example.com":"+2010..."} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
        <label className="block text-sm font-semibold">{t("reports.reportTitle")}<input value={title} onChange={e=>setTitle(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
        <label className="block text-sm font-semibold">{t("reports.content")}<textarea value={body} onChange={e=>setBody(e.target.value)} placeholder="{t("reports.contentPlaceholder")}" className="mt-1 min-h-28 w-full rounded-lg border bg-background p-3"/></label>
        <button disabled={deliveryLoading||!destination||!body} className="rounded-lg bg-primary px-5 py-2 text-primary-foreground">{deliveryLoading?"{t("reports.sending")}":"{t("reports.sendNow")}"}</button>
      </form>
    </div>

    {result&&<div><h2 className="mb-2 font-semibold">{t("reports.analysisResult")}</h2><pre className="overflow-auto rounded-2xl bg-slate-950 p-5 text-xs text-white">{result}</pre></div>}

    <form onSubmit={createSchedule} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
      <div><h2 className="font-semibold">{t("reports.scheduleReport")}</h2><p className="text-xs text-muted-foreground">يدعم: every:15m، every:2h، daily:09:00، weekly:MON@09:00، monthly:15@09:00، quarterly:1@09:00.</p></div>
      <div className="grid gap-3 md:grid-cols-3">
        <input value={schedule} onChange={e=>setSchedule(e.target.value)} placeholder="daily:09:00" className="rounded-lg border bg-background p-2"/>
        <input value={destination} onChange={e=>setDestination(e.target.value)} placeholder="{t("reports.destination")}" className="rounded-lg border bg-background p-2"/>
        <button disabled={deliveryLoading||!destination} className="rounded-lg border px-4 py-2">{deliveryLoading?"{t("reports.saving")}":"{t("reports.saveSchedule")}"}</button>
      </div>
    </form>

    <div className="rounded-2xl border bg-card p-5 shadow-sm">
      <h2 className="mb-4 font-semibold">{t("reports.currentSchedules")}</h2>
      {schedules.length===0?<p className="text-sm text-muted-foreground">لا توجد جدولات لهذه {t("reports.company")}.</p>:<div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b text-right"><th className="p-2">{t("reports.channel")}</th><th className="p-2">{t("reports.destination")}</th><th className="p-2">الجدول</th><th className="p-2">الحالة</th><th className="p-2">{t("reports.nextRun")}</th></tr></thead><tbody>{schedules.map(s=><tr key={s.id} className="border-b last:border-0"><td className="p-2">{s.channel}</td><td className="p-2">{s.destination}</td><td className="p-2">{s.schedule}</td><td className="p-2">{s.last_status||t("reports.scheduled")}</td><td className="p-2">{s.next_run_at?formatCompanyDateTime(s.next_run_at,dateFormat):"—"}</td></tr>)}</tbody></table></div>}
    </div>
  </section>;
}
