import { FormEvent, useEffect, useState } from "react";
import client from "@/shared/api/client";

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

  useEffect(()=>{loadSchedules();},[companyId]);

  async function loadSchedules(){
    if(!companyId){setSchedules([]);return;}
    try{const r=await client.get("/reports/schedules",{params:{company_id:companyId}});setSchedules(r.data||[]);}
    catch(e:any){setError(e?.response?.data?.detail||"تعذر تحميل جدولة التقارير");}
  }

  async function analyze(e:FormEvent){
    e.preventDefault();setLoading(true);setError("");
    try{
      const parsed=JSON.parse(metrics);
      if(!companyId){throw new Error("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");}
      if(fromDate&&toDate&&fromDate>toDate){throw new Error("تاريخ البداية لا يمكن أن يكون بعد تاريخ النهاية.");}
      const r=await client.post("/reports/ai/analyze",{company_id:companyId,domain:"general",metrics:parsed,question:question||null,from_date:fromDate||null,to_date:toDate||null});
      setResult(JSON.stringify(r.data,null,2));
      setBody(JSON.stringify(r.data,null,2));
    }catch(e:any){setError(e?.message==="Unexpected end of JSON input"?"صيغة Metrics JSON غير صحيحة":e?.response?.data?.detail||e?.message||"تعذر تحليل التقرير");}
    finally{setLoading(false);}
  }

  async function deliver(e:FormEvent){
    if(!companyId){setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");return;}
    e.preventDefault();setDeliveryLoading(true);setError("");
    try{
      await client.post("/reports/deliver",{company_id:companyId,channel,destination,title,body:body||result||"PrimeERP report"});
      setError(""); alert("تم إرسال التقرير بنجاح");
    }catch(e:any){setError(e?.response?.data?.detail||"تعذر إرسال التقرير");}
    finally{setDeliveryLoading(false);}
  }

  async function createSchedule(e:FormEvent){
    if(!companyId){setError("اختر شركة فعالة أولاً؛ لا يتم استخدام شركة افتراضية.");return;}
    e.preventDefault();setDeliveryLoading(true);setError("");
    try{
      await client.post("/reports/schedules",{company_id:companyId,code:"management_snapshot",name:title,report_type:"snapshot",channel,destination,schedule,format:"text",parameters:{},filters:{}});
      await loadSchedules();
    }catch(e:any){setError(e?.response?.data?.detail||"تعذر إنشاء الجدولة");}
    finally{setDeliveryLoading(false);}
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">التقارير والتحليلات</h1>
      <p className="mt-1 text-sm text-muted-foreground">تحليل مؤشرات الأعمال بالـAI، إرسال التقارير، وجدولة التسليم عبر البريد أو WhatsApp.</p>
    </header>

    {error&&<div className="rounded-lg bg-destructive/10 p-3 text-sm">{error}</div>}

    <div className="grid gap-6 lg:grid-cols-2">
      <form onSubmit={analyze} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <div><h2 className="font-semibold">تحليل ذكي</h2><p className="text-xs text-muted-foreground">القواعد الرقابية تعمل حتى عند عدم تفعيل مزود AI.</p></div>
        <label className="block text-sm font-semibold">سؤال التحليل<textarea value={question} onChange={e=>setQuestion(e.target.value)} placeholder="ما أهم المخاطر في المؤشرات الحالية؟" className="mt-1 min-h-24 w-full rounded-lg border bg-background p-3"/></label>
        <div className="grid gap-3 sm:grid-cols-2"><label className="text-sm font-semibold">من تاريخ<input type="date" value={fromDate} onChange={e=>setFromDate(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label><label className="text-sm font-semibold">إلى تاريخ<input type="date" value={toDate} onChange={e=>setToDate(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label></div>
        <label className="block text-sm font-semibold">Metrics JSON<textarea value={metrics} onChange={e=>setMetrics(e.target.value)} className="mt-1 min-h-32 w-full rounded-lg border bg-background p-3 font-mono text-xs"/></label>
        <button disabled={loading} className="rounded-lg bg-primary px-5 py-2 text-primary-foreground">{loading?"جارٍ التحليل...":"تحليل المؤشرات"}</button>
      </form>

      <form onSubmit={deliver} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        <div><h2 className="font-semibold">إرسال تقرير</h2><p className="text-xs text-muted-foreground">يتطلب إعداد SMTP أو WhatsApp في بيئة التشغيل.</p></div>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="text-sm font-semibold">الشركة<input type="number" min="1" value={companyId} onChange={e=>setCompanyId(Number(e.target.value)||0)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
          <label className="text-sm font-semibold">القناة<select value={channel} onChange={e=>setChannel(e.target.value as "email"|"whatsapp")} className="mt-1 w-full rounded-lg border bg-background p-2"><option value="email">Email</option><option value="whatsapp">WhatsApp</option></select></label>
        </div>
        <label className="block text-sm font-semibold">المستلم<input value={destination} onChange={e=>setDestination(e.target.value)} placeholder={channel==="email"?"manager@example.com":"+2010..."} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
        <label className="block text-sm font-semibold">عنوان التقرير<input value={title} onChange={e=>setTitle(e.target.value)} className="mt-1 w-full rounded-lg border bg-background p-2"/></label>
        <label className="block text-sm font-semibold">المحتوى<textarea value={body} onChange={e=>setBody(e.target.value)} placeholder="حلل المؤشرات أولاً أو اكتب محتوى التقرير هنا." className="mt-1 min-h-28 w-full rounded-lg border bg-background p-3"/></label>
        <button disabled={deliveryLoading||!destination||!body} className="rounded-lg bg-primary px-5 py-2 text-primary-foreground">{deliveryLoading?"جارٍ الإرسال...":"إرسال الآن"}</button>
      </form>
    </div>

    {result&&<div><h2 className="mb-2 font-semibold">نتيجة التحليل</h2><pre className="overflow-auto rounded-2xl bg-slate-950 p-5 text-xs text-white">{result}</pre></div>}

    <form onSubmit={createSchedule} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
      <div><h2 className="font-semibold">جدولة التقرير</h2><p className="text-xs text-muted-foreground">يدعم: every:15m، every:2h، daily:09:00، weekly:MON@09:00، monthly:15@09:00، quarterly:1@09:00.</p></div>
      <div className="grid gap-3 md:grid-cols-3">
        <input value={schedule} onChange={e=>setSchedule(e.target.value)} placeholder="daily:09:00" className="rounded-lg border bg-background p-2"/>
        <input value={destination} onChange={e=>setDestination(e.target.value)} placeholder="المستلم" className="rounded-lg border bg-background p-2"/>
        <button disabled={deliveryLoading||!destination} className="rounded-lg border px-4 py-2">{deliveryLoading?"جارٍ الحفظ...":"حفظ الجدولة"}</button>
      </div>
    </form>

    <div className="rounded-2xl border bg-card p-5 shadow-sm">
      <h2 className="mb-4 font-semibold">الجدولات الحالية</h2>
      {schedules.length===0?<p className="text-sm text-muted-foreground">لا توجد جدولات لهذه الشركة.</p>:<div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b text-right"><th className="p-2">القناة</th><th className="p-2">المستلم</th><th className="p-2">الجدول</th><th className="p-2">الحالة</th><th className="p-2">التشغيل القادم</th></tr></thead><tbody>{schedules.map(s=><tr key={s.id} className="border-b last:border-0"><td className="p-2">{s.channel}</td><td className="p-2">{s.destination}</td><td className="p-2">{s.schedule}</td><td className="p-2">{s.last_status||"scheduled"}</td><td className="p-2">{s.next_run_at?new Date(s.next_run_at).toLocaleString("ar-EG"):"-"}</td></tr>)}</tbody></table></div>}
    </div>
  </section>;
}
