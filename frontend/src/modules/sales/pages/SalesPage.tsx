import { FormEvent, useEffect, useState } from "react";
import { salesApi, type Document, type Partner } from "../api/commercial.api";

const today = () => new Date().toISOString().slice(0, 10);
const errorText = (e: any) => e?.response?.data?.detail || e?.message || "حدث خطأ غير متوقع.";

export default function SalesPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<Document | null>(null);
  const [form, setForm] = useState({ partner_id:"", item_id:"", quantity:"1", unit_price:"0", number:"", document_date:today(), document_type:"order", source_order_id:"", source_line_id:"" });
  const load = async () => { setLoading(true); setError(""); try { const [d,p] = await Promise.all([salesApi.list(), salesApi.partners()]); setDocs(d); setPartners(p); } catch(e) { setError(errorText(e)); } finally { setLoading(false); } };
  useEffect(() => { void load(); }, []);
  const create = async (e: FormEvent) => { e.preventDefault(); setBusy(true); setError(""); try {
    await salesApi.create({ partner_id:Number(form.partner_id), document_type:form.document_type, number:form.number.trim(), document_date:form.document_date, ...(form.source_order_id ? { source_order_id:Number(form.source_order_id) } : {}), lines:[{ item_id:Number(form.item_id), quantity:Number(form.quantity), unit_price:Number(form.unit_price), discount_percent:0, tax_percent:0, ...(form.source_line_id ? { source_sales_line_id:Number(form.source_line_id) } : {}) }] });
    setForm({...form, number:"", item_id:"", quantity:"1", unit_price:"0", source_order_id:"", source_line_id:""}); await load();
  } catch(e) { setError(errorText(e)); } finally { setBusy(false); } };
  const action = async (id:number, fn:(id:number)=>Promise<Document>) => { setBusy(true); setError(""); try { const updated=await fn(id); setSelected(updated); await load(); } catch(e) { setError(errorText(e)); } finally { setBusy(false); } };
  return <section className="space-y-5 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">المبيعات</h1><p className="text-sm text-muted-foreground">إنشاء المستند، اعتماده، ترحيل المخزون والتحصيل من نفس دورة البيع.</p></header>
    {error && <div className="rounded-xl border bg-destructive/10 p-3 text-sm">{error}</div>}
    <form onSubmit={create} className="grid gap-3 rounded-2xl border p-4 md:grid-cols-6">
      <select className="rounded-lg border p-2" value={form.partner_id} onChange={e=>setForm({...form,partner_id:e.target.value})} required><option value="">العميل</option>{partners.map(p=><option key={p.id} value={p.id}>{p.name}</option>)}</select>
      <select className="rounded-lg border p-2" value={form.document_type} onChange={e=>setForm({...form,document_type:e.target.value})}><option value="quotation">عرض سعر</option><option value="order">طلب بيع</option><option value="delivery">إذن تسليم</option><option value="invoice">فاتورة</option></select>
      <input className="rounded-lg border p-2" placeholder="رقم المستند" value={form.number} onChange={e=>setForm({...form,number:e.target.value})} required />
      <input className="rounded-lg border p-2" type="date" value={form.document_date} onChange={e=>setForm({...form,document_date:e.target.value})} required />
      {["delivery","invoice"].includes(form.document_type)&&<><input className="rounded-lg border p-2" type="number" min="1" placeholder="رقم أمر البيع" value={form.source_order_id} onChange={e=>setForm({...form,source_order_id:e.target.value})}/><input className="rounded-lg border p-2" type="number" min="1" placeholder="رقم بند أمر البيع" value={form.source_line_id} onChange={e=>setForm({...form,source_line_id:e.target.value})}/></>}
      <input className="rounded-lg border p-2" type="number" min="1" placeholder="Item ID" value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})} required />
      <input className="rounded-lg border p-2" type="number" min="0" step="0.01" placeholder="السعر" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})} required />
      <input className="rounded-lg border p-2" type="number" min="0.0001" step="0.0001" placeholder="الكمية" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})} required />
      <button disabled={busy} className="rounded-lg border px-4 py-2 font-medium disabled:opacity-50">{busy?"جارٍ التنفيذ...":"إنشاء مستند"}</button>
    </form>
    {loading ? <div className="rounded-2xl border p-8 text-center">جارٍ التحميل...</div> : <div className="overflow-auto rounded-2xl border"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40"><th className="p-3 text-right">رقم</th><th className="p-3 text-right">النوع</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">الإجمالي</th><th className="p-3 text-right">إجراءات</th></tr></thead><tbody>{docs.map(d=><tr key={d.id} className="border-b"><td className="p-3">{d.number}</td><td className="p-3">{d.document_type}</td><td className="p-3">{d.status}</td><td className="p-3">{d.total}</td><td className="p-3 flex gap-2">{(d.status==="draft"||d.status==="approved")&&<button disabled={busy} className="rounded-lg border px-3 py-1" onClick={()=>void action(d.id,salesApi.confirm)}>تأكيد</button>}{d.status==="pending_approval"&&<><button disabled={busy} className="rounded-lg border px-3 py-1" onClick={()=>void action(d.id,id=>salesApi.decideApproval(id,"approve"))}>موافقة</button><button disabled={busy} className="rounded-lg border px-3 py-1 text-destructive" onClick={()=>void action(d.id,id=>salesApi.decideApproval(id,"reject"))}>رفض</button></>}{d.document_type==="delivery"&&["confirmed","partially_fulfilled"].includes(d.status)&&<button disabled={busy} className="rounded-lg border px-3 py-1" onClick={()=>void action(d.id,salesApi.postInventory)}>ترحيل المخزون</button>}{["confirmed","posted","approved"].includes(d.status)&&Number(d.total)>Number(d.paid_total)&&<button disabled={busy} className="rounded-lg border px-3 py-1" onClick={()=>void action(d.id,id=>salesApi.pay(id,Number(d.total)-Number(d.paid_total),"cash"))}>تحصيل كامل</button>}<button className="rounded-lg border px-3 py-1" onClick={()=>setSelected(d)}>تفاصيل</button></td></tr>)}</tbody></table></div>}
    {selected&&<div className="rounded-2xl border p-4"><div className="flex justify-between"><b>المستند #{selected.number}</b><button onClick={()=>setSelected(null)}>إغلاق</button></div><p className="mt-2 text-sm">العميل: {partners.find(p=>p.id===selected.partner_id)?.name || selected.partner_id} — الإجمالي: {selected.total} — المدفوع: {selected.paid_total}</p></div>}
  </section>;
}