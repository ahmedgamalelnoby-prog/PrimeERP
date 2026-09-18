import { useEffect, useState } from "react";
import client from "@/shared/api/client";

type Move = {
  id:number; item_id:number; source_location_id:number|null; destination_location_id:number|null;
  quantity:string; unit_cost:string; movement_type:string; transaction_date:string|null;
  reference:string|null; status:string; accounting_entry_id:number|null;
};

const API = "/inventory/stock-moves";

export default function InventoryTransactionsPage() {
  const [companyId,setCompanyId]=useState(() => localStorage.getItem("company_id") || "");
  const [moves,setMoves]=useState<Move[]>([]);
  const [loading,setLoading]=useState(false);
  const [message,setMessage]=useState("");
  const [form,setForm]=useState({item_id:"",source_location_id:"",destination_location_id:"",quantity:"",unit_cost:"0",movement_type:"receipt",reference:"",notes:""});

  async function load(){
    setLoading(true); setMessage("");
    try {
      const r=await fetch(`${API}?company_id=${encodeURIComponent(companyId)}`);
      if(!r.ok) throw new Error(await r.text());
      setMoves(await r.json());
    } catch(e){ setMessage(e instanceof Error?e.message:"تعذر تحميل حركات المخزون"); }
    finally{setLoading(false);}
  }
  useEffect(()=>{void load();},[]);

  async function create(){
    try{
      const payload={company_id:Number(companyId),item_id:Number(form.item_id),source_location_id:form.source_location_id?Number(form.source_location_id):null,destination_location_id:form.destination_location_id?Number(form.destination_location_id):null,quantity:form.quantity,unit_cost:form.unit_cost,movement_type:form.movement_type,reference:form.reference||null,notes:form.notes||null};
      const r=await fetch(API,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
      if(!r.ok) throw new Error(await r.text());
      setMessage("تم إنشاء حركة مخزون مسودة."); setForm({...form,item_id:"",source_location_id:"",destination_location_id:"",quantity:"",reference:"",notes:""}); await load();
    }catch(e){setMessage(e instanceof Error?e.message:"تعذر إنشاء الحركة");}
  }
  async function action(id:number,kind:"post"|"reverse"){
    try{
      const r=await fetch(`${API}/${id}/${kind}?company_id=${encodeURIComponent(companyId)}`,{method:"POST"});
      if(!r.ok) throw new Error(await r.text());
      setMessage(kind==="post"?"تم ترحيل الحركة.":"تم عكس الحركة."); await load();
    }catch(e){setMessage(e instanceof Error?e.message:"تعذر تنفيذ العملية");}
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">حركات المخزون</h1><p className="mt-1 text-sm text-muted-foreground">إنشاء الحركات وترحيلها وعكس الحركات المرحلة مع ربطها بالتكلفة والمحاسبة.</p></header>
    <div className="rounded-2xl border bg-card p-5">
      <div className="grid gap-3 md:grid-cols-4">
        <label>الشركة<input className="mt-1 w-full rounded-lg border p-2" value={companyId} onChange={e=>setCompanyId(e.target.value)}/></label>
        <label>الصنف<input className="mt-1 w-full rounded-lg border p-2" value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})}/></label>
        <label>الكمية<input className="mt-1 w-full rounded-lg border p-2" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})}/></label>
        <label>نوع الحركة<select className="mt-1 w-full rounded-lg border p-2" value={form.movement_type} onChange={e=>setForm({...form,movement_type:e.target.value})}><option value="receipt">استلام</option><option value="issue">صرف</option><option value="transfer">تحويل</option><option value="adjustment">تسوية</option><option value="opening">رصيد افتتاحي</option><option value="return">مرتجع</option></select></label>
        <label>موقع المصدر<input className="mt-1 w-full rounded-lg border p-2" value={form.source_location_id} onChange={e=>setForm({...form,source_location_id:e.target.value})}/></label>
        <label>موقع الوجهة<input className="mt-1 w-full rounded-lg border p-2" value={form.destination_location_id} onChange={e=>setForm({...form,destination_location_id:e.target.value})}/></label>
        <label>تكلفة الوحدة<input className="mt-1 w-full rounded-lg border p-2" value={form.unit_cost} onChange={e=>setForm({...form,unit_cost:e.target.value})}/></label>
        <label>المرجع<input className="mt-1 w-full rounded-lg border p-2" value={form.reference} onChange={e=>setForm({...form,reference:e.target.value})}/></label>
      </div>
      <button className="mt-4 rounded-lg bg-primary px-4 py-2 text-primary-foreground" onClick={create}>إنشاء حركة</button>
    </div>
    {message && <div className="rounded-lg border p-3 text-sm">{message}</div>}
    <div className="overflow-x-auto rounded-2xl border">
      <table className="w-full text-sm"><thead><tr className="border-b"><th className="p-3">#</th><th>الصنف</th><th>النوع</th><th>الكمية</th><th>التاريخ</th><th>الحالة</th><th>إجراء</th></tr></thead>
      <tbody>{moves.map(m=><tr className="border-b" key={m.id}><td className="p-3">{m.id}</td><td>{m.item_id}</td><td>{m.movement_type}</td><td>{m.quantity}</td><td>{m.transaction_date||"-"}</td><td>{m.status}</td><td className="space-x-2 space-x-reverse">{m.status==="draft"&&<button className="rounded border px-3 py-1" onClick={()=>action(m.id,"post")}>ترحيل</button>}{m.status==="posted"&&<button className="rounded border px-3 py-1" onClick={()=>action(m.id,"reverse")}>عكس</button>}</td></tr>)}</tbody></table>
      {!loading && moves.length===0 && <div className="p-6 text-center text-muted-foreground">لا توجد حركات.</div>}
    </div>
    <button className="rounded-lg border px-4 py-2" onClick={()=>void load()}>تحديث</button>
  </section>;
}
