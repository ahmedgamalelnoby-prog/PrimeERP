import { useEffect, useMemo, useState } from "react";
import { Calculator, ExternalLink, Plus, RefreshCw, Truck, Wallet } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import client from "@/shared/api/client";
import { formatCompanyDate, useCompanyDateFormat } from "@/utils/format-date";

type Carrier = { id:number; company_id:number; code:string; name:string; is_active:boolean };
type Profile = { id:number; carrier_id:number; name:string; effective_from:string; effective_to?:string|null; priority:number; is_active:boolean };
type Shipment = { id:number; tracking_no:string; carrier_id:number; status:string; customer_name:string; cod_amount:number|string; shipping_fee:number|string; shipment_date?:string|null };
type Position = { carrier_id:number; carrier_name:string; shipment_count:number; unsettled_count:number; cod_receivable:string; carrier_payable:string; settled_net:string; settled_fees:string; net_position:string; position:string };

export default function ShippingPage() {
 const dateFormat = useCompanyDateFormat();
  const companyId = Number(localStorage.getItem("company_id")) || 0;
  const [carriers,setCarriers]=useState<Carrier[]>([]);
  const [profiles,setProfiles]=useState<Profile[]>([]);
  const [shipments,setShipments]=useState<Shipment[]>([]);
  const [positions,setPositions]=useState<Position[]>([]);
  const [selectedCarrier,setSelectedCarrier]=useState<number|null>(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState("");
  const [newCarrier,setNewCarrier]=useState({code:"",name:""});
  const [newProfile,setNewProfile]=useState({name:"",effective_from:new Date().toISOString().slice(0,10),priority:"100"});

  const load=async()=>{
    if(!companyId)return;
    setLoading(true);setError("");
    try{
      const [c,s,p]=await Promise.all([
        client.get<Carrier[]>(`/shipping/carriers?company_id=${companyId}`),
        client.get<Shipment[]>(`/shipping/shipments?company_id=${companyId}`),
        client.get<Profile[]>(`/shipping/pricing/profiles?company_id=${companyId}`),
      ]);
      setCarriers(c.data);setShipments(s.data);setProfiles(p.data);
      if(!selectedCarrier && c.data[0])setSelectedCarrier(c.data[0].id);
      const report=await client.get<Position[]>(`/shipping/reports/carrier-position?company_id=${companyId}&date_basis=shipment`);
      setPositions(report.data);
    }catch(e:any){setError(e?.response?.data?.detail||"Unable to load Shipping data.");}
    finally{setLoading(false);}
  };
  useEffect(()=>{void load();},[companyId]);

  const carrierProfiles=useMemo(()=>profiles.filter(p=>p.carrier_id===selectedCarrier),[profiles,selectedCarrier]);

  const createCarrier=async()=>{
    if(!newCarrier.code||!newCarrier.name)return;
    try{
      await client.post("/shipping/carriers",{company_id:companyId,code:newCarrier.code,name:newCarrier.name});
      setNewCarrier({code:"",name:""});await load();
    }catch(e:any){setError(e?.response?.data?.detail||"Could not create carrier.");}
  };
  const createProfile=async()=>{
    if(!selectedCarrier||!newProfile.name)return;
    try{
      await client.post("/shipping/pricing/profiles",{company_id:companyId,carrier_id:selectedCarrier,name:newProfile.name,effective_from:newProfile.effective_from,priority:Number(newProfile.priority)});
      setNewProfile({name:"",effective_from:new Date().toISOString().slice(0,10),priority:"100"});await load();
    }catch(e:any){setError(e?.response?.data?.detail||"Could not create pricing profile.");}
  };

  if(!companyId)return <div className="p-8">Select an active company first.</div>;

  return <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8" dir="rtl">
    <div className="mx-auto max-w-7xl space-y-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><div className="flex items-center gap-2 text-sm font-semibold text-blue-700"><Truck className="size-4"/>Shipping</div>
          <h1 className="mt-1 text-3xl font-black">الشحن والتسويات</h1>
          <p className="mt-2 text-sm text-slate-500">شركات الشحن، عقود التسعير، الطلبات، وتحديد الرصيد المستحق لكل شركة.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={()=>void load()} disabled={loading}><RefreshCw className="me-2 size-4"/>تحديث</Button>
          <Button variant="outline" onClick={()=>window.location.assign("/shipping/pricing")}><Calculator className="me-2 size-4"/>تسعير الشحن</Button><Button variant="outline" onClick={()=>window.location.assign("/shipping/settlements")}><Wallet className="me-2 size-4"/>التسويات</Button><Button variant="outline" onClick={()=>window.location.assign("/shipping/settings")}><ExternalLink className="me-2 size-4"/>حالات الشحن</Button>
        </div>
      </div>

      {error&&<div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      <div className="grid gap-4 md:grid-cols-4">
        <Card className="rounded-2xl"><CardContent className="p-5"><div className="text-sm text-slate-500">شركات الشحن</div><div className="mt-2 text-3xl font-black">{carriers.length}</div></CardContent></Card>
        <Card className="rounded-2xl"><CardContent className="p-5"><div className="text-sm text-slate-500">الشحنات</div><div className="mt-2 text-3xl font-black">{shipments.length}</div></CardContent></Card>
        <Card className="rounded-2xl"><CardContent className="p-5"><div className="text-sm text-slate-500">عقود التسعير</div><div className="mt-2 text-3xl font-black">{profiles.length}</div></CardContent></Card>
        <Card className="rounded-2xl"><CardContent className="p-5"><div className="text-sm text-slate-500">شحنات غير مسواة</div><div className="mt-2 text-3xl font-black">{positions.reduce((n,x)=>n+x.unsettled_count,0)}</div></CardContent></Card>
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <Card className="rounded-2xl"><CardHeader><CardTitle>شركات الشحن</CardTitle></CardHeader><CardContent className="space-y-3">
          {carriers.map(c=><button key={c.id} onClick={()=>setSelectedCarrier(c.id)} className={"w-full rounded-xl border p-4 text-start "+(c.id===selectedCarrier?"border-blue-500 bg-blue-50":"bg-white")}><div className="font-bold">{c.name}</div><div className="text-xs text-slate-500">{c.code}</div></button>)}
          <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"><Input placeholder="Code" value={newCarrier.code} onChange={e=>setNewCarrier({...newCarrier,code:e.target.value})}/><Input placeholder="اسم شركة الشحن" value={newCarrier.name} onChange={e=>setNewCarrier({...newCarrier,name:e.target.value})}/><Button onClick={()=>void createCarrier()}><Plus className="size-4"/></Button></div>
        </CardContent></Card>

        <Card className="rounded-2xl"><CardHeader><CardTitle>عقود / Profiles التسعير</CardTitle></CardHeader><CardContent className="space-y-3">
          {carrierProfiles.map(p=><div key={p.id} className="rounded-xl border bg-white p-4"><div className="font-bold">{p.name}</div><div className="mt-1 text-xs text-slate-500">من {p.effective_from}{p.effective_to?` إلى ${p.effective_to}`:""} · أولوية {p.priority}</div></div>)}
          <div className="grid gap-2 sm:grid-cols-[1fr_150px_90px_auto]"><Input placeholder="اسم العقد" value={newProfile.name} onChange={e=>setNewProfile({...newProfile,name:e.target.value})}/><Input type="date" value={newProfile.effective_from} onChange={e=>setNewProfile({...newProfile,effective_from:e.target.value})}/><Input type="number" value={newProfile.priority} onChange={e=>setNewProfile({...newProfile,priority:e.target.value})}/><Button onClick={()=>void createProfile()} disabled={!selectedCarrier}><Plus className="size-4"/></Button></div>
          {selectedCarrier&&<div className="text-xs text-slate-500">بعد إنشاء الـProfile، افتح «تسعير الشحن» لإضافة قواعد الوزن/المنطقة/COD/الـtier والمرتجع والتخزين.</div>}
        </CardContent></Card>
      </div>

      <Card className="rounded-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><Wallet className="size-5"/>مركز شركة الشحن</CardTitle></CardHeader><CardContent className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-sm"><thead><tr className="border-b text-start"><th className="p-3 text-start">الشركة</th><th className="p-3 text-start">COD مستحق</th><th className="p-3 text-start">تكاليف/رسوم</th><th className="p-3 text-start">صافي المحول</th><th className="p-3 text-start">غير مسوى</th><th className="p-3 text-start">المركز</th></tr></thead>
          <tbody>{positions.map(x=><tr key={x.carrier_id} className="border-b"><td className="p-3 font-semibold">{x.carrier_name}</td><td className="p-3">{x.cod_receivable}</td><td className="p-3">{x.carrier_payable}</td><td className="p-3">{x.settled_net}</td><td className="p-3">{x.unsettled_count}</td><td className="p-3 font-bold">{x.position==="carrier_owes_company"?"شركة الشحن لها مستحقات لنا":x.position==="company_owes_carrier"?"علينا مستحقات للشركة":"مسوى"}</td></tr>)}</tbody>
        </table>
      </CardContent></Card>

      <Card className="rounded-2xl"><CardHeader><CardTitle className="flex items-center gap-2"><Calculator className="size-5"/>آخر الشحنات</CardTitle></CardHeader><CardContent className="overflow-x-auto">
        <table className="w-full min-w-[760px] text-sm"><thead><tr className="border-b"><th className="p-3 text-start">Tracking</th><th className="p-3 text-start">العميل</th><th className="p-3 text-start">الحالة</th><th className="p-3 text-start">COD</th><th className="p-3 text-start">تكلفة الشحن</th><th className="p-3 text-start">التاريخ</th></tr></thead>
          <tbody>{shipments.slice(0,20).map(s=><tr key={s.id} className="border-b"><td className="p-3 font-semibold">{s.tracking_no}</td><td className="p-3">{s.customer_name}</td><td className="p-3">{s.status}</td><td className="p-3">{s.cod_amount}</td><td className="p-3">{s.shipping_fee}</td><td className="p-3">{s.shipment_date ? formatCompanyDate(s.shipment_date, dateFormat) : "-"}</td></tr>)}</tbody>
        </table>
      </CardContent></Card>
    </div>
  </div>;
}
