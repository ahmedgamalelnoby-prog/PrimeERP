import { useEffect, useMemo, useState } from "react";
import { ArrowRight, Check, Plus, Save, Truck } from "lucide-react";
import { useTranslation } from "react-i18next";
import client from "@/shared/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type Status = { id:number; company_id:number; code:string; name:string; name_ar?:string|null; parent_code?:string|null; sort_order:number; is_active:boolean; financial_actions:string[]; allowed_next_codes:string[] };
const actions = [
  ["recognize_revenue","Recognize order revenue / إثبات إيراد الطلب"],["recognize_shipping_revenue","Recognize shipping revenue / إثبات إيراد الشحن"],
  ["recognize_shipping_cost","Recognize carrier cost / إثبات تكلفة شركة الشحن"],["create_cod_receivable","Create COD receivable / إثبات مستحقات COD"],
  ["recognize_cod_fee","Recognize COD commission / إثبات عمولة COD"],["recognize_card_fee","Recognize card fee / إثبات رسوم البطاقة"],
  ["reverse_revenue","Reverse revenue / عكس الإيراد"],["reverse_shipping_revenue","Reverse shipping revenue / عكس إيراد الشحن"],
  ["reverse_cod_receivable","Reverse COD receivable / عكس مستحقات COD"],["recognize_return_cost","Recognize return cost / إثبات تكلفة المرتجع"],
] as const;

export default function ShippingStatusSettingsPage() {
  const { i18n } = useTranslation();
  const ar=(i18n.resolvedLanguage ?? i18n.language).startsWith("ar");
  const companyId=Number(localStorage.getItem("company_id"))||0;
  const [statuses,setStatuses]=useState<Status[]>([]),[selected,setSelected]=useState<number|null>(null),[loading,setLoading]=useState(true),[saving,setSaving]=useState(false),[message,setMessage]=useState("");
  const current=useMemo(()=>statuses.find(x=>x.id===selected)??statuses[0],[statuses,selected]);
  useEffect(()=>{ if(!companyId)return; setLoading(true); client.get<Status[]>("/shipping/order-statuses?company_id="+companyId).then(r=>{setStatuses(r.data);if(r.data[0])setSelected(r.data[0].id)}).finally(()=>setLoading(false)); },[companyId]);
  const save=async()=>{if(!current)return;setSaving(true);setMessage("");try{const r=await client.put<Status>("/shipping/order-statuses/"+current.id,{...current,company_id:companyId});setStatuses(xs=>xs.map(x=>x.id===r.data.id?r.data:x));setMessage(ar?"تم حفظ الإعدادات.":"Settings saved.");}catch{setMessage(ar?"تعذر الحفظ. راجع الصلاحيات والبيانات.":"Could not save. Check permissions and data.");}finally{setSaving(false)}};
  const patch=(fn:(x:Status)=>Status)=>setStatuses(xs=>xs.map(x=>x.id===current.id?fn(x):x));
  if(!companyId)return <div className="p-8">{ar?"اختر شركة نشطة أولًا.":"Select an active company first."}</div>;
  if(loading)return <div className="p-8">{ar?"جاري التحميل...":"Loading..."}</div>;
  if(!current)return <div className="p-8">{ar?"لا توجد حالات شحن.":"No shipping statuses found."}</div>;
  return <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8" dir={ar?"rtl":"ltr"}>
    <div className="mx-auto max-w-7xl">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div><div className="flex items-center gap-2 text-sm font-semibold text-blue-700"><Truck className="size-4"/>Shipping</div><h1 className="mt-1 text-3xl font-black">{ar?"إعدادات حالات الشحن":"Shipping Status Settings"}</h1><p className="mt-2 text-sm text-slate-500">{ar?"حدد دورة الطلب والإجراءات المالية التي تعمل تلقائيًا عند كل حالة.":"Configure the order lifecycle and financial actions triggered by each status."}</p></div>
        <Button onClick={()=>void save()} disabled={saving} className="rounded-xl"><Save className="me-2 size-4"/>{saving?(ar?"جاري الحفظ...":"Saving..."):(ar?"حفظ":"Save")}</Button>
      </div>
      {message&&<div className="mb-4 rounded-xl border bg-white px-4 py-3 text-sm">{message}</div>}
      <div className="grid gap-5 lg:grid-cols-[320px_1fr]">
        <Card className="rounded-2xl"><CardHeader><CardTitle>{ar?"حالات الطلب":"Order statuses"}</CardTitle></CardHeader><CardContent className="space-y-2">
          {statuses.map(s=><button key={s.id} onClick={()=>setSelected(s.id)} className={"w-full rounded-xl border px-4 py-3 text-start "+(s.id===current.id?"border-blue-500 bg-blue-50":"bg-white")}><div className="font-bold">{ar?(s.name_ar||s.name):s.name}</div><div className="mt-1 text-xs text-slate-500">{s.code} · {s.allowed_next_codes.length} {ar?"انتقالات":"transitions"}</div></button>)}
          <div className="rounded-xl border border-dashed p-3 text-xs text-slate-500"><Plus className="mb-1 size-4"/>{ar?"إنشاء الحالات الجديدة متاح عبر API مع نفس الصلاحيات.":"New custom statuses can be created through the API with the same permission model."}</div>
        </CardContent></Card>
        <Card className="rounded-2xl"><CardHeader><CardTitle>{ar?"تفاصيل الحالة":"Status details"}</CardTitle></CardHeader><CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-semibold">{ar?"الاسم":"Name"}<Input className="mt-2" value={current.name} onChange={e=>patch(x=>({...x,name:e.target.value}))}/></label>
            <label className="text-sm font-semibold">{ar?"الاسم بالعربية":"Arabic name"}<Input className="mt-2" value={current.name_ar??""} onChange={e=>patch(x=>({...x,name_ar:e.target.value}))}/></label>
          </div>
          <div><div className="mb-2 text-sm font-semibold">{ar?"الحالات التالية المسموح بها":"Allowed next statuses"}</div><div className="flex flex-wrap gap-2">{statuses.filter(s=>s.id!==current.id).map(s=>{const on=current.allowed_next_codes.includes(s.code);return <button key={s.id} onClick={()=>patch(x=>({...x,allowed_next_codes:on?x.allowed_next_codes.filter(c=>c!==s.code):[...x.allowed_next_codes,s.code]}))} className={"rounded-full border px-3 py-1.5 text-xs font-semibold "+(on?"border-blue-500 bg-blue-50 text-blue-700":"bg-white text-slate-600")}>{on&&<Check className="me-1 inline size-3"/>}{ar?(s.name_ar||s.name):s.name}</button>})}</div></div>
          <div><div className="mb-2 text-sm font-semibold">{ar?"الإجراءات المالية عند الوصول للحالة":"Financial actions on entry"}</div><div className="grid gap-2 sm:grid-cols-2">{actions.map(([key,label])=>{const on=current.financial_actions.includes(key);return <button key={key} onClick={()=>patch(x=>({...x,financial_actions:on?x.financial_actions.filter(a=>a!==key):[...x.financial_actions,key]}))} className={"rounded-xl border p-3 text-start text-xs font-semibold "+(on?"border-emerald-400 bg-emerald-50":"bg-white")}>{on?<Check className="me-2 inline size-4 text-emerald-600"/>:<ArrowRight className="me-2 inline size-4 text-slate-400"/>}{label}</button>})}</div></div>
          <label className="flex items-center gap-3 text-sm font-semibold"><input type="checkbox" checked={current.is_active} onChange={e=>patch(x=>({...x,is_active:e.target.checked}))}/>{ar?"الحالة نشطة":"Status is active"}</label>
        </CardContent></Card>
      </div>
    </div>
  </div>;
}
