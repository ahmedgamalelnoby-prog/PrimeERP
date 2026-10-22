import { useEffect, useMemo, useState } from "react";
import { arApApi, type AgingRow, type AgingSummary } from "../api/arAp.api";
import { formatCompanyDate, useCompanyClockDate, useCompanyDateFormat } from "@/utils/format-date";
const money=(v:string|number)=>Number(v||0).toLocaleString("en-US",{minimumFractionDigits:2,maximumFractionDigits:2});
const bucketOrder=["current","1-30","31-60","61-90","91+"];

export default function ARAgingPage(){
 const dateFormat=useCompanyDateFormat();
 const {companyDate,loading:clockLoading,error:clockError}=useCompanyClockDate();
 const [asOf,setAsOf]=useState(""); const [data,setData]=useState<AgingSummary|null>(null); const [loading,setLoading]=useState(false); const [error,setError]=useState("");
 async function load(){if(!asOf)return;setLoading(true);setError("");try{setData((await arApApi.aging(asOf)).data)}catch(e:any){setError(e?.response?.data?.detail||e?.message||"تعذر تحميل أعمار الذمم")}finally{setLoading(false)}}
 useEffect(()=>{if(asOf)void load()},[asOf]);
 useEffect(()=>{if(companyDate)setAsOf(current=>current||companyDate)},[companyDate]);
 const buckets=useMemo(()=>{const out:Record<string,{receivable:number;payable:number}>={};for(const b of bucketOrder)out[b]={receivable:0,payable:0};for(const r of data?.rows||[]){const b=out[r.bucket]||(out[r.bucket]={receivable:0,payable:0});b[r.direction==="receivable"?"receivable":"payable"]+=Number(r.outstanding)}return out},[data]);
 const rows=(data?.rows||[]) as AgingRow[];
 return <section className="space-y-6 p-6" dir="rtl">
  <header className="flex flex-col gap-3 md:flex-row md:items-end md:justify-between"><div><h1 className="text-2xl font-bold">أعمار الذمم المدينة والدائنة</h1><p className="text-sm text-muted-foreground">AR/AP Aging حسب تاريخ الاستحقاق، مع كشف المستندات غير المسددة.</p></div><div className="flex gap-2"><input type="date" value={asOf} onChange={e=>setAsOf(e.target.value)} className="rounded border p-2"/><button onClick={()=>void load()} disabled={loading||clockLoading||!asOf} className="rounded bg-primary px-4 py-2 text-primary-foreground">{loading?"جارٍ التحميل":"تحديث"}</button></div></header>
  {(error||clockError)&&<div className="rounded-xl border p-3 text-sm">{error||clockError}</div>}
  <div className="grid gap-4 md:grid-cols-3"><div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">الذمم المدينة</div><div className="mt-2 text-2xl font-bold">{money(data?.receivable||0)}</div></div><div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">الذمم الدائنة</div><div className="mt-2 text-2xl font-bold">{money(data?.payable||0)}</div></div><div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">الصافي</div><div className="mt-2 text-2xl font-bold">{money(data?.net||0)}</div></div></div>
  <div className="rounded-2xl border bg-card p-4"><h2 className="mb-3 font-semibold">الأعمار</h2><div className="grid gap-3 md:grid-cols-5">{bucketOrder.map(b=><div key={b} className="rounded-xl border p-3"><div className="text-sm font-medium">{b==="current"?"حالي":b+" يوم"}</div><div className="mt-2 text-sm">مدين: {money(buckets[b]?.receivable||0)}</div><div className="text-sm">دائن: {money(buckets[b]?.payable||0)}</div></div>)}</div></div>
  <div className="overflow-auto rounded-2xl border bg-card"><table className="w-full min-w-[900px] text-sm"><thead><tr className="border-b text-right"><th className="p-3">الاتجاه</th><th className="p-3">المستند</th><th className="p-3">الشريك</th><th className="p-3">تاريخ المستند</th><th className="p-3">الاستحقاق</th><th className="p-3">الإجمالي</th><th className="p-3">المسدد</th><th className="p-3">المتبقي</th><th className="p-3">متأخر</th><th className="p-3">الفئة</th></tr></thead><tbody>{rows.map(r=><tr key={r.direction+"-"+r.document_id} className="border-b"><td className="p-3">{r.direction==="receivable"?"مدين":"دائن"}</td><td className="p-3">{r.document_number}</td><td className="p-3">#{r.partner_id}</td><td className="p-3">{formatCompanyDate(r.document_date, dateFormat)}</td><td className="p-3">{formatCompanyDate(r.due_date, dateFormat)}</td><td className="p-3">{money(r.total)}</td><td className="p-3">{money(r.paid_total)}</td><td className="p-3 font-semibold">{money(r.outstanding)}</td><td className="p-3">{r.days_overdue}</td><td className="p-3">{r.bucket}</td></tr>)}{!loading&&!rows.length&&<tr><td colSpan={10} className="p-8 text-center text-muted-foreground">لا توجد ذمم مستحقة في التاريخ المحدد.</td></tr>}</tbody></table></div>
 </section>;
}
