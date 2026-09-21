import { FormEvent, useEffect, useState } from "react";
import api from "@/shared/api/client";

type Order={id:number;order_number:string;customer_id:number;status:string;order_date:string;grand_total:string;lines:{product_id:number;quantity:string;unit_price:string;line_total:string}[]};
type Customer={id:number;code:string;name:string};
type Product={id:number;sku:string;name:string;sale_price:string};
export default function SalesOrdersPage({createOnly=false}:{createOnly?:boolean}){
 const [orders,setOrders]=useState<Order[]>([]),[customers,setCustomers]=useState<Customer[]>([]),[products,setProducts]=useState<Product[]>([]);
 const [form,setForm]=useState({company_id:"",branch_id:"",customer_id:"",product_id:"",quantity:"1",unit_price:"",order_date:new Date().toISOString().slice(0,10)});
 const [message,setMessage]=useState("");
 const load=async()=>{const [o,c,p]=await Promise.all([api.get("/sales/sales-orders"),api.get("/customers"),api.get("/products")]);setOrders(o.data);setCustomers(c.data);setProducts(p.data);};
 useEffect(()=>{load().catch(()=>setMessage("تعذر تحميل بيانات المبيعات"));},[]);
 const submit=async(e:FormEvent)=>{e.preventDefault();setMessage("");try{await api.post("/sales/sales-orders",{company_id:Number(form.company_id),branch_id:Number(form.branch_id),customer_id:Number(form.customer_id),order_date:form.order_date,lines:[{product_id:Number(form.product_id),quantity:Number(form.quantity),unit_price:Number(form.unit_price)}]});setMessage("تم إنشاء طلب المبيعات");await load();}catch(err:any){setMessage(err?.response?.data?.detail??"تعذر إنشاء الطلب");}};
 return <div className="space-y-6 p-6" dir="rtl"><div><h1 className="text-2xl font-bold">طلبات المبيعات</h1><p className="text-sm text-muted-foreground">طلب مبيعات مرتبط بالعميل والمنتج والفرع داخل نفس الـTenant.</p></div>
 <form onSubmit={submit} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-3">
  <input className="rounded-lg border p-2" placeholder="Company ID" value={form.company_id} onChange={e=>setForm({...form,company_id:e.target.value})} required/>
  <input className="rounded-lg border p-2" placeholder="Branch ID" value={form.branch_id} onChange={e=>setForm({...form,branch_id:e.target.value})} required/>
  <select className="rounded-lg border p-2" value={form.customer_id} onChange={e=>setForm({...form,customer_id:e.target.value})} required><option value="">العميل</option>{customers.map(c=><option key={c.id} value={c.id}>{c.code} — {c.name}</option>)}</select>
  <select className="rounded-lg border p-2" value={form.product_id} onChange={e=>{const p=products.find(x=>x.id===Number(e.target.value));setForm({...form,product_id:e.target.value,unit_price:p?.sale_price??""})}} required><option value="">المنتج</option>{products.map(p=><option key={p.id} value={p.id}>{p.sku} — {p.name}</option>)}</select>
  <input className="rounded-lg border p-2" type="number" min="0.001" step="0.001" placeholder="الكمية" value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})} required/>
  <input className="rounded-lg border p-2" type="number" min="0" step="0.01" placeholder="السعر" value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})} required/>
  <input className="rounded-lg border p-2" type="date" value={form.order_date} onChange={e=>setForm({...form,order_date:e.target.value})}/>
  <button className="rounded-lg bg-primary px-4 py-2 text-primary-foreground" type="submit">إنشاء طلب</button>{message&&<div className="text-sm md:col-span-2">{message}</div>}
 </form>
 {!createOnly&&<div className="overflow-auto rounded-2xl border"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-3 text-right">رقم الطلب</th><th className="p-3 text-right">العميل</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">الإجمالي</th></tr></thead><tbody>{orders.map(o=><tr key={o.id} className="border-b"><td className="p-3">{o.order_number}</td><td className="p-3">{customers.find(c=>c.id===o.customer_id)?.name??o.customer_id}</td><td className="p-3">{o.status}</td><td className="p-3">{o.grand_total}</td></tr>)}</tbody></table></div>}</div>;
}