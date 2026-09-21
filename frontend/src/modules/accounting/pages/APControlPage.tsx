import {useEffect,useState} from "react";
import client from "@/shared/api/client";
import {apApi} from "../api/apApi";
type Partner={id:number;name:string;code?:string;partner_type:string};
export default function APControlPage(){
 const [partners,setPartners]=useState<Partner[]>([]),[partnerId,setPartnerId]=useState(""),[result,setResult]=useState<any>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 const company=()=>Number(localStorage.getItem("company_id"));
 const load=async()=>{try{const r=await client.get<Partner[]>("/commerce/partners",{params:{company_id:company(),partner_type:"vendor"}});setPartners(r.data);if(!partnerId&&r.data[0])setPartnerId(String(r.data[0].id));}catch(e:any){setError(e?.response?.data?.detail||e?.message||"تعذر تحميل الموردين")}};
 useEffect(()=>{void load()},[]);
 const run=async(fn:()=>Promise<any>)=>{setBusy(true);setError("");try{setResult((await fn()).data)}catch(e:any){setError(e?.response?.data?.detail||e?.message||"حدث خطأ")}finally{setBusy(false)}};
 return <section className="space-y-6 p-6" dir="rtl"><header><h1 className="text-2xl font-bold">مركز الذمم الدائنة AP</h1><p className="text-sm text-muted-foreground">Aging، Supplier Statement، 3-Way Match، Variance، Write-off، وGL Reconciliation.</p></header>
 {error&&<div className="rounded-xl border p-3 text-sm text-destructive">{error}</div>}
 <div className="grid gap-3 rounded-2xl border bg-card p-4 md:grid-cols-4"><select className="rounded-lg border p-2" value={partnerId} onChange={e=>setPartnerId(e.target.value)}><option value="">المورد</option>{partners.map(p=><option key={p.id} value={p.id}>{p.code?p.code+" — ":""}{p.name}</option>)}</select>
 <button className="rounded-lg border px-4 py-2" disabled={!partnerId||busy} onClick={()=>void run(()=>apApi.aging(Number(partnerId)))}>Aging المورد</button>
 <button className="rounded-lg border px-4 py-2" disabled={!partnerId||busy} onClick={()=>void run(()=>apApi.statement(Number(partnerId)))}>كشف حساب المورد</button>
 <button className="rounded-lg border px-4 py-2" disabled={busy} onClick={()=>void run(()=>apApi.reconcile(partnerId?Number(partnerId):undefined))}>مطابقة AP مع GL</button></div>
 {result&&<pre className="overflow-auto rounded-2xl border bg-muted/20 p-4 text-xs">{JSON.stringify(result,null,2)}</pre>}</section>
}