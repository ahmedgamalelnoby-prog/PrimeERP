import { useEffect, useMemo, useState } from "react";
import { ArrowRight, CheckCircle2, Save, Wallet } from "lucide-react";
import client from "@/shared/api/client";
import { formatCompanyDate, useCompanyDateFormat } from "@/utils/format-date";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Carrier={id:number;name:string;code:string};
type Shipment={id:number;tracking_no:string;carrier_id:number;status:string;customer_name:string;cod_amount:number|string;shipment_date?:string|null};
type Line={shipment_id:number;collected_amount:string;carrier_fee:string;cod_commission:string;withdrawal_fee:string;other_fee:string};
type Batch={id:number;carrier_id:number;reference:string;settlement_date:string;gross_amount:string;carrier_fees:string;net_amount:string;status:string};

const n=(v:string|number)=>Number(v||0);
const emptyLine=(s:Shipment):Line=>({shipment_id:s.id,collected_amount:"0",carrier_fee:"0",cod_commission:"0",withdrawal_fee:"0",other_fee:"0"});

export default function ShippingSettlementPage(){
 const dateFormat = useCompanyDateFormat();
 const companyId=Number(localStorage.getItem("company_id"))||0;
 const [carriers,setCarriers]=useState<Carrier[]>([]),[shipments,setShipments]=useState<Shipment[]>([]),[batches,setBatches]=useState<Batch[]>([]);
 const [carrierId,setCarrierId]=useState(0),[selected,setSelected]=useState<Record<number,Line>>({}),[reference,setReference]=useState(""),[settlementDate,setSettlementDate]=useState(new Date().toISOString().slice(0,10)),[error,setError]=useState(""),[saving,setSaving]=useState(false);

 const load=async()=>{
  if(!companyId)return;
  setError("");
  try{
   const c=await client.get<Carrier[]>(`/shipping/carriers?company_id=${companyId}`);
   setCarriers(c.data);
   const cid=carrierId||c.data[0]?.id||0;
   setCarrierId(cid);
   if(cid){
    const [s,b]=await Promise.all([
     client.get<Shipment[]>(`/shipping/shipments?company_id=${companyId}&carrier_id=${cid}&status=delivered`),
     client.get<Batch[]>(`/shipping/settlements?company_id=${companyId}&carrier_id=${cid}`)
    ]);
    setShipments(s.data);
    setBatches(b.data);
   }else{setShipments([]);setBatches([]);}
  }catch(e:any){setError(e?.response?.data?.detail||"تعذر تحميل التسويات.")}
 };

 useEffect(()=>{void load()},[companyId]);

 const chooseCarrier=async(id:number)=>{
  setCarrierId(id);setSelected({});setError("");
  if(!id){setShipments([]);setBatches([]);return;}
  try{
   const [s,b]=await Promise.all([
    client.get<Shipment[]>(`/shipping/shipments?company_id=${companyId}&carrier_id=${id}&status=delivered`),
    client.get<Batch[]>(`/shipping/settlements?company_id=${companyId}&carrier_id=${id}`)
   ]);
   setShipments(s.data);setBatches(b.data);
  }catch(e:any){setError(e?.response?.data?.detail||"تعذر تحميل الشحنات.")}
 };

 const toggle=(s:Shipment)=>{
  setSelected(x=>{
   const next={...x};
   if(next[s.id]) delete next[s.id]; else next[s.id]=emptyLine(s);
   return next;
  });
 };
 const allSelected=shipments.length>0&&shipments.every(s=>Boolean(selected[s.id]));
 const toggleAll=()=>setSelected(x=>{
  if(allSelected)return {};
  return Object.fromEntries(shipments.map(s=>[s.id,x[s.id]||emptyLine(s)]));
 });

 const rows=Object.values(selected);
 const totals=useMemo(()=>rows.reduce((a,x)=>{
  const collected=n(x.collected_amount);
  const fee=(n(x.cod_commission)+n(x.withdrawal_fee)+n(x.other_fee))||n(x.carrier_fee);
  a.expected+=n(shipments.find(s=>s.id===x.shipment_id)?.cod_amount||0);
  a.collected+=collected;a.fees+=fee;a.net+=collected-fee;return a;
 },{expected:0,collected:0,fees:0,net:0}),[rows,shipments]);

 const update=(id:number,key:keyof Line,value:string)=>{
  setSelected(x=>({...x,[id]:{...(x[id]||{shipment_id:id,collected_amount:"0",carrier_fee:"0",cod_commission:"0",withdrawal_fee:"0",other_fee:"0"}),[key]:value}}));
 };

 const submit=async()=>{
  if(!carrierId||!reference.trim()||!rows.length)return;
  setSaving(true);setError("");
  try{
   await client.post("/shipping/settlements",{company_id:companyId,carrier_id:carrierId,reference,settlement_date:settlementDate,lines:rows,notes:"Created from Shipping settlement workspace"});
   setSelected({});setReference("");await load();
  }catch(e:any){setError(e?.response?.data?.detail||"تعذر إنشاء التسوية.")}finally{setSaving(false)}
 };

 if(!companyId)return <div className="p-8">اختر شركة نشطة أولًا.</div>;
 return <div dir="rtl" className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8"><div className="mx-auto max-w-7xl space-y-5">
  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><div className="text-sm font-semibold text-blue-700">Shipping / Settlement</div><h1 className="mt-1 text-3xl font-black">تسويات شركات الشحن</h1><p className="mt-2 text-sm text-slate-500">مطابقة COD المحصل مع مستحقات الشركة، العمولات، رسوم السحب، وصافي التحويل.</p></div><Button variant="outline" onClick={()=>window.location.assign("/shipping")}><ArrowRight className="me-2 size-4"/>الشحن</Button></div>
  {error&&<div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
  <Card className="rounded-2xl"><CardContent className="grid gap-3 p-5 md:grid-cols-3"><select className="h-10 rounded-md border bg-white px-3" value={carrierId} onChange={e=>void chooseCarrier(Number(e.target.value))}><option value="0">اختر شركة الشحن</option>{carriers.map(c=><option key={c.id} value={c.id}>{c.name} ({c.code})</option>)}</select><Input placeholder="مرجع التسوية" value={reference} onChange={e=>setReference(e.target.value)}/><Input type="date" value={settlementDate} onChange={e=>setSettlementDate(e.target.value)}/></CardContent></Card>
  <div className="grid gap-4 md:grid-cols-4"><Card><CardContent className="p-5"><div className="text-sm text-slate-500">COD المتوقع</div><div className="mt-2 text-2xl font-black">{totals.expected.toFixed(2)}</div></CardContent></Card><Card><CardContent className="p-5"><div className="text-sm text-slate-500">المحصل</div><div className="mt-2 text-2xl font-black">{totals.collected.toFixed(2)}</div></CardContent></Card><Card><CardContent className="p-5"><div className="text-sm text-slate-500">الرسوم</div><div className="mt-2 text-2xl font-black">{totals.fees.toFixed(2)}</div></CardContent></Card><Card><CardContent className="p-5"><div className="text-sm text-slate-500">صافي التحويل</div><div className="mt-2 text-2xl font-black">{totals.net.toFixed(2)}</div></CardContent></Card></div>
  <Card className="rounded-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><Wallet className="size-5"/>الشحنات Delivered غير المسواة</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[1200px] text-sm"><thead><tr className="border-b"><th className="p-3 text-center"><input type="checkbox" checked={allSelected} onChange={toggleAll} aria-label="اختيار الكل"/></th><th className="p-3 text-start">Tracking</th><th className="p-3 text-start">العميل</th><th className="p-3 text-start">COD</th><th className="p-3 text-start">المحصل</th><th className="p-3 text-start">عمولة COD</th><th className="p-3 text-start">رسوم Visa/سحب</th><th className="p-3 text-start">أخرى</th><th className="p-3 text-start">صافي</th></tr></thead><tbody>{shipments.map(s=>{const isSelected=Boolean(selected[s.id]);const x=selected[s.id]||emptyLine(s);const fee=(n(x.cod_commission)+n(x.withdrawal_fee)+n(x.other_fee))||n(x.carrier_fee);return <tr className={`border-b ${isSelected?"bg-slate-50":""}`} key={s.id}><td className="p-3 text-center"><input type="checkbox" checked={isSelected} onChange={()=>toggle(s)} aria-label={`اختيار الشحنة ${s.tracking_no}`}/></td><td className="p-3 font-semibold">{s.tracking_no}</td><td className="p-3">{s.customer_name}</td><td className="p-3">{s.cod_amount}</td><td className="p-2"><Input type="number" min="0" value={x.collected_amount} disabled={!isSelected} onChange={e=>update(s.id,"collected_amount",e.target.value)}/></td><td className="p-2"><Input type="number" min="0" value={x.cod_commission} disabled={!isSelected} onChange={e=>update(s.id,"cod_commission",e.target.value)}/></td><td className="p-2"><Input type="number" min="0" value={x.withdrawal_fee} disabled={!isSelected} onChange={e=>update(s.id,"withdrawal_fee",e.target.value)}/></td><td className="p-2"><Input type="number" min="0" value={x.other_fee} disabled={!isSelected} onChange={e=>update(s.id,"other_fee",e.target.value)}/></td><td className="p-3 font-bold">{(n(x.collected_amount)-fee).toFixed(2)}</td></tr>})}</tbody></table>{!shipments.length&&<div className="p-8 text-center text-sm text-slate-500">لا توجد شحنات Delivered غير مسواة لهذه الشركة.</div>}</CardContent></Card>
  <div className="flex items-center justify-between gap-3"><div className="text-sm text-slate-500">تم اختيار {rows.length} شحنة للتسوية.</div><Button onClick={()=>void submit()} disabled={saving||!carrierId||!reference.trim()||!rows.length}><Save className="me-2 size-4"/>{saving?"جاري إنشاء التسوية...":"إنشاء Settlement Batch"}</Button></div>
  <Card className="rounded-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><CheckCircle2 className="size-5"/>آخر التسويات</CardTitle></CardHeader><CardContent className="overflow-x-auto"><table className="w-full min-w-[800px] text-sm"><thead><tr className="border-b"><th className="p-3 text-start">المرجع</th><th className="p-3 text-start">التاريخ</th><th className="p-3 text-start">الإجمالي</th><th className="p-3 text-start">الرسوم</th><th className="p-3 text-start">الصافي</th><th className="p-3 text-start">الحالة</th></tr></thead><tbody>{batches.map(b=><tr className="border-b" key={b.id}><td className="p-3 font-semibold">{b.reference}</td><td className="p-3">{formatCompanyDate(b.settlement_date, dateFormat)}</td><td className="p-3">{b.gross_amount}</td><td className="p-3">{b.carrier_fees}</td><td className="p-3 font-bold">{b.net_amount}</td><td className="p-3">{b.status}</td></tr>)}</tbody></table></CardContent></Card>
 </div></div>;
}
