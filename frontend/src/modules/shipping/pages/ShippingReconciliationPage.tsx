import { useEffect, useState } from "react";
import { ArrowRight, RefreshCw, Truck } from "lucide-react";
import client from "@/shared/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Carrier={id:number;name:string;code:string};
type Position={carrier_id:number;carrier_name:string;cod_receivable:string;carrier_payable:string;settled_gross:string;settled_fees:string;settled_net:string;revenue:string;shipment_count:number;unsettled_count:number;net_position:string;position:string};

export default function ShippingReconciliationPage(){
 const companyId=Number(localStorage.getItem("company_id"))||0;
 const [carriers,setCarriers]=useState<Carrier[]>([]),[rows,setRows]=useState<Position[]>([]);
 const [carrierId,setCarrierId]=useState(0),[dateFrom,setDateFrom]=useState(""),[dateTo,setDateTo]=useState(""),[basis,setBasis]=useState<"shipment"|"order">("shipment"),[error,setError]=useState(""),[loading,setLoading]=useState(false);
 const load=async()=>{
  if(!companyId)return;
  setLoading(true);setError("");
  try{
   const c=await client.get<Carrier[]>(`/shipping/carriers?company_id=${companyId}`);
   setCarriers(c.data);
   const p=new URLSearchParams({company_id:String(companyId),date_basis:basis});
   if(carrierId)p.set("carrier_id",String(carrierId));
   if(dateFrom)p.set("date_from",dateFrom);
   if(dateTo)p.set("date_to",dateTo);
   const r=await client.get<Position[]>(`/shipping/reports/carrier-position?${p.toString()}`);
   setRows(r.data);
  }catch(e:any){setError(e?.response?.data?.detail||"تعذر تحميل تقرير التسويات.")}finally{setLoading(false)}
 };
 useEffect(()=>{void load()},[companyId,basis]);
 if(!companyId)return <div className="p-8">اختر شركة نشطة أولًا.</div>;
 return <div dir="rtl" className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8"><div className="mx-auto max-w-7xl space-y-5">
  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><div className="text-sm font-semibold text-blue-700">Shipping / Reconciliation</div><h1 className="mt-1 text-3xl font-black">موقف شركات الشحن والتسويات</h1><p className="mt-2 text-sm text-slate-500">اعرض الموقف حسب تاريخ الطلب أو تاريخ الشحن، واعرف هل الشركة لها مستحقات أم عليها مستحقات لشركة الشحن.</p></div><Button variant="outline" onClick={()=>window.location.assign("/shipping")}><ArrowRight className="me-2 size-4"/>الشحن</Button></div>
  {error&&<div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
  <Card className="rounded-2xl"><CardContent className="grid gap-3 p-5 md:grid-cols-5"><select className="h-10 rounded-md border bg-white px-3" value={carrierId} onChange={e=>setCarrierId(Number(e.target.value))}><option value="0">كل شركات الشحن</option>{carriers.map(c=><option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}</select><select className="h-10 rounded-md border bg-white px-3" value={basis} onChange={e=>setBasis(e.target.value as "shipment"|"order")}><option value="shipment">حسب تاريخ الشحن</option><option value="order">حسب تاريخ الطلب</option></select><Input type="date" value={dateFrom} onChange={e=>setDateFrom(e.target.value)} placeholder="من"/><Input type="date" value={dateTo} onChange={e=>setDateTo(e.target.value)} placeholder="إلى"/><Button onClick={()=>void load()} disabled={loading}><RefreshCw className={`me-2 size-4 ${loading?"animate-spin":""}`}/>تحديث التقرير</Button></CardContent></Card>
  <Card className="rounded-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><Truck className="size-5"/>موقف شركات الشحن</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[1250px] text-sm"><thead><tr className="border-b"><th className="p-3 text-start">شركة الشحن</th><th className="p-3 text-start">COD مستحق من الشركة</th><th className="p-3 text-start">تكاليف/رسوم مستحقة للشركة</th><th className="p-3 text-start">إجمالي المحصل</th><th className="p-3 text-start">الرسوم المخصومة</th><th className="p-3 text-start">صافي التحويل</th><th className="p-3 text-start">الرصيد</th><th className="p-3 text-start">الموقف</th><th className="p-3 text-start">غير مسوى</th></tr></thead><tbody>{rows.map(r=><tr className="border-b" key={r.carrier_id}><td className="p-3 font-semibold">{r.carrier_name}</td><td className="p-3">{r.cod_receivable}</td><td className="p-3">{r.carrier_payable}</td><td className="p-3">{r.settled_gross}</td><td className="p-3">{r.settled_fees}</td><td className="p-3 font-bold">{r.settled_net}</td><td className="p-3 font-bold">{r.net_position}</td><td className="p-3">{r.position==="carrier_owes_company"?"شركة الشحن عليها":"company_owes_carrier"===r.position?"علينا لشركة الشحن":"متسوى"}</td><td className="p-3">{r.unsettled_count}</td></tr>)} </tbody></table>{!rows.length&&<div className="p-8 text-center text-sm text-slate-500">لا توجد بيانات ضمن الفلاتر الحالية.</div>}</CardContent></Card>
 </div></div>;
}
