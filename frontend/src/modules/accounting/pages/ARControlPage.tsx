import { useEffect, useState } from "react";
import client from "@/shared/api/client";
import { arApi } from "../api/arAp.api";

type Payment={id:number;document_id:number|null;partner_id?:number|null;amount:string|number;status:string;payment_date:string};
type Partner={id:number;name:string;code?:string;partner_type:string};

export default function ARControlPage(){
 const [payments,setPayments]=useState<Payment[]>([]),[partners,setPartners]=useState<Partner[]>([]),[partnerId,setPartnerId]=useState(""),[paymentId,setPaymentId]=useState(""),[result,setResult]=useState<any>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 const company=()=>Number(localStorage.getItem("company_id"));
 const load=async()=>{try{const c=company();const [p,ps]=await Promise.all([client.get<Payment[]>("/commerce/payments",{params:{company_id:c,document_kind:"sale"}}),client.get<Partner[]>("/commerce/partners",{params:{company_id:c,partner_type:"customer"}})]);setPayments(p.data);setPartners(ps.data);if(!partnerId&&ps.data[0])setPartnerId(String(ps.data[0].id));}catch(e:any){setError(e?.response?.data?.detail||e?.message||"تعذر تحميل بيانات AR");}};
 useEffect(()=>{void load()},[]);
 const run=async(fn:()=>Promise<any>)=>{setBusy(true);setError("");try{setResult((await fn()).data);await load()}catch(e:any){setError(e?.response?.data?.detail||e?.message||"حدث خطأ")}finally{setBusy(false)}};
 return <section className="space-y-6 p-6" dir="rtl">
  <header><h1 className="text-2xl font-bold">مركز الذمم المدينة AR</h1><p className="text-sm text-muted-foreground">Allocation، Auto-match، الدفعات غير المخصصة، الائتمان، والمطابقة.</p></header>
  {error&&<div className="rounded-xl border p-3 text-sm text-destructive">{error}</div>}
  <div className="grid gap-3 rounded-2xl border bg-card p-4 md:grid-cols-4">
   <select className="rounded-lg border p-2" value={partnerId} onChange={e=>setPartnerId(e.target.value)}><option value="">العميل</option>{partners.map(p=><option key={p.id} value={p.id}>{p.code?p.code+" — ":""}{p.name}</option>)}</select>
   <button className="rounded-lg border px-4 py-2" disabled={!partnerId||busy} onClick={()=>void run(()=>arApi.credit(Number(partnerId)))}>فحص الحد الائتماني</button>
   <button className="rounded-lg border px-4 py-2" disabled={!partnerId||busy} onClick={()=>void run(()=>arApi.reconcile(Number(partnerId)))}>مطابقة AR</button>
   <button className="rounded-lg border px-4 py-2" disabled={busy} onClick={()=>void run(()=>arApi.reconcile())}>مطابقة كل العملاء</button>
  </div>
  <div className="overflow-auto rounded-2xl border bg-card"><table className="w-full min-w-[850px] text-sm"><thead><tr className="border-b text-right"><th className="p-3">الدفع</th><th className="p-3">التاريخ</th><th className="p-3">الفاتورة</th><th className="p-3">المبلغ</th><th className="p-3">إجراءات</th></tr></thead><tbody>{payments.map(p=><tr key={p.id} className="border-b"><td className="p-3">PAY-{p.id}</td><td className="p-3">{p.payment_date}</td><td className="p-3">{p.document_id??"دفعة مقدمة"}</td><td className="p-3">{p.amount}</td><td className="p-3 flex gap-2"><button className="rounded border px-3 py-1" onClick={()=>{setPaymentId(String(p.id));setResult(null)}}>اختيار</button>{p.document_id&&<button className="rounded border px-3 py-1" disabled={busy} onClick={()=>void run(()=>arApi.autoMatch(p.id,p.partner_id||Number(partnerId)))}>Auto-match</button>}</td></tr>)}{!payments.length&&<tr><td colSpan={5} className="p-8 text-center">لا توجد دفعات.</td></tr>}</tbody></table></div>
  {paymentId&&<div className="rounded-2xl border bg-card p-4"><div className="font-semibold">الدفع المختار: PAY-{paymentId}</div><button className="mt-3 rounded-lg border px-4 py-2" disabled={busy} onClick={()=>void run(()=>arApi.unapplied(Number(paymentId)))}>عرض الرصيد غير المخصص</button></div>}
  {result&&<pre className="overflow-auto rounded-2xl border bg-muted/20 p-4 text-xs">{JSON.stringify(result,null,2)}</pre>}
 </section>
}
