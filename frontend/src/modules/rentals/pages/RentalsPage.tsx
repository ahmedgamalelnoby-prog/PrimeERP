import {useState} from "react";
import {useRentals} from "../hooks/useRentals";
export default function RentalsPage(){
 const {contracts,charges,loading,reload,activate,terminate,charge}=useRentals();const [busy,setBusy]=useState<number|null>(null);const [error,setError]=useState("");
 const act=async(fn:()=>Promise<unknown>,id:number)=>{setBusy(id);setError("");try{await fn();await reload()}catch(e:any){setError(e?.response?.data?.detail??e?.message??"حدث خطأ")}finally{setBusy(null)}};
 return <div dir="rtl" className="mx-auto w-full max-w-[1600px] space-y-6">
  <header><h1 className="text-2xl font-bold">التأجير التجاري</h1><p className="mt-1 text-sm text-muted-foreground">العقود والمطالبات والربط المحاسبي.</p></header>
  {error&&<div className="rounded-xl border p-3 text-sm">{error}</div>}
  <section className="grid gap-4 md:grid-cols-3">
   <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">العقود</div><div className="mt-2 text-3xl font-bold">{contracts.length}</div></div>
   <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">العقود النشطة</div><div className="mt-2 text-3xl font-bold">{contracts.filter(c=>c.status==="active").length}</div></div>
   <div className="rounded-2xl border bg-card p-5"><div className="text-sm text-muted-foreground">إجمالي المطالبات</div><div className="mt-2 text-3xl font-bold">{charges.reduce((s,c)=>s+Number(c.total_amount),0).toLocaleString("ar-EG")} EGP</div></div>
  </section>
  <section className="rounded-2xl border bg-card p-5">
   <div className="mb-4 flex items-center justify-between"><h2 className="font-semibold">العقود</h2><button className="rounded-lg border px-3 py-2 text-sm" onClick={()=>void reload()}>{loading?"جاري...":"تحديث"}</button></div>
   <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="border-b text-right"><th className="p-3">العقد</th><th className="p-3">الفترة</th><th className="p-3">الحالة</th><th className="p-3">التسعير</th><th className="p-3">إجراءات</th></tr></thead><tbody>
   {contracts.map(c=><tr key={c.id} className="border-b"><td className="p-3 font-medium">{c.number}</td><td className="p-3">{c.start_date} → {c.end_date}</td><td className="p-3">{c.status}</td><td className="p-3">{c.pricing_type}</td><td className="p-3 flex gap-2">
    {c.status==="draft"&&<button disabled={busy===c.id} className="rounded-lg border px-3 py-1.5" onClick={()=>void act(()=>activate(c.id),c.id)}>تفعيل</button>}
    {c.status==="active"&&<><button disabled={busy===c.id} className="rounded-lg border px-3 py-1.5" onClick={()=>void act(()=>terminate(c.id),c.id)}>إنهاء</button><button disabled={busy===c.id} className="rounded-lg border px-3 py-1.5" onClick={()=>void act(()=>charge({contract_id:c.id,charge_date:new Date().toISOString().slice(0,10),period_start:c.start_date,period_end:c.end_date,revenue_amount:0}),c.id)}>إنشاء مطالبة</button></>}
   </td></tr>)}
   </tbody></table></div>
  </section>
 </div>;
}
