import { useState } from "react";
import client from "@/shared/api/client";

type Row = { item_id:number; variant_id:number|null; warehouse_id:number; quantity_on_hand:string|number; average_cost:string|number; inventory_value:string|number };

export default function InventoryCostingPage() {
  const [companyId,setCompanyId]=useState(() => localStorage.getItem("company_id") || "");
  const [warehouseId,setWarehouseId]=useState("");
  const [itemId,setItemId]=useState("");
  const [rows,setRows]=useState<Row[]>([]);
  const [total,setTotal]=useState<string|number>("0");
  const [message,setMessage]=useState("");

  const load=async()=>{
    try {
      const r=await client.get("/inventory/costing/valuation",{params:{company_id:Number(companyId),warehouse_id:warehouseId?Number(warehouseId):undefined,item_id:itemId?Number(itemId):undefined}});
      setRows(r.data.rows || []); setTotal(r.data.total_value || 0); setMessage("");
    } catch(e){setMessage(e instanceof Error?e.message:"تعذر تحميل تقييم المخزون");}
  };

  const reconcile=async()=>{
    try {
      if(!warehouseId || !itemId) throw new Error("أدخل Warehouse ID و Item ID لإجراء المطابقة.");
      const r=await client.post("/inventory/completion/cost-reconciliation",undefined,{params:{company_id:Number(companyId),warehouse_id:Number(warehouseId),item_id:Number(itemId),method:"weighted_average"}});
      setMessage(`نتيجة المطابقة: ${r.data.status} — الفرق ${r.data.difference}`);
    } catch(e){setMessage(e instanceof Error?e.message:"تعذر إجراء المطابقة");}
  };

  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">تقييم وتكلفة المخزون</h1><p className="mt-1 text-sm text-muted-foreground">Weighted Average / FIFO / Standard / Actual مع مطابقة قيمة الـSubledger.</p></header>
    <div className="grid gap-3 rounded-2xl border p-5 md:grid-cols-4">
      <input className="rounded-lg border p-2" value={companyId} onChange={e=>setCompanyId(e.target.value)} placeholder="Company ID"/>
      <input className="rounded-lg border p-2" value={warehouseId} onChange={e=>setWarehouseId(e.target.value)} placeholder="Warehouse ID"/>
      <input className="rounded-lg border p-2" value={itemId} onChange={e=>setItemId(e.target.value)} placeholder="Item ID (اختياري للتقييم)"/>
      <div className="flex gap-2"><button className="rounded-lg border px-4 py-2" onClick={()=>void load()}>تقييم</button><button className="rounded-lg border px-4 py-2" onClick={()=>void reconcile()}>مطابقة</button></div>
    </div>
    {message&&<div className="rounded-lg border p-3 text-sm">{message}</div>}
    <div className="rounded-2xl border p-5"><span className="text-sm text-muted-foreground">إجمالي القيمة</span><div className="text-2xl font-bold">{total}</div></div>
    <div className="overflow-auto rounded-2xl border"><table className="w-full text-right text-sm"><thead><tr className="border-b"><th className="p-3">الصنف</th><th>Variant</th><th>المخزن</th><th>الكمية</th><th>التكلفة</th><th>القيمة</th></tr></thead><tbody>{rows.map((x,i)=><tr className="border-b" key={i}><td className="p-3">{x.item_id}</td><td>{x.variant_id ?? "-"}</td><td>{x.warehouse_id}</td><td>{x.quantity_on_hand}</td><td>{x.average_cost}</td><td>{x.inventory_value}</td></tr>)}</tbody></table></div>
  </section>;
}
