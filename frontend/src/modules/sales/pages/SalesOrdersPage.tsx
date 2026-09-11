import { useEffect, useState } from "react";

interface SalesOrder { id: number; order_number: string; customer_id: number; warehouse_id: number; order_date: string; status: string; total_amount: string; reference?: string | null; }

export default function SalesOrdersPage() {
  const [companyId, setCompanyId] = useState("1");
  const [orders, setOrders] = useState<SalesOrder[]>([]);
  const load = () => fetch(`/api/v1/sales/orders?company_id=${encodeURIComponent(companyId)}`).then(r => r.ok ? r.json() : []).then(setOrders).catch(() => setOrders([]));
  useEffect(load, [companyId]);
  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">طلبات المبيعات</h1><p className="mt-1 text-sm text-muted-foreground">طلبات المبيعات هي نقطة الربط بين العميل والحجز والشحن والمخزون والذمم المدينة.</p></header>
    <div className="flex gap-3"><input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={e => setCompanyId(e.target.value)} placeholder="Company ID" /><button className="rounded-lg border px-4 py-2" onClick={load}>تحديث</button></div>
    <div className="overflow-hidden rounded-2xl border bg-card"><table className="w-full text-right text-sm"><thead><tr className="border-b"><th className="p-3">رقم الطلب</th><th className="p-3">العميل</th><th className="p-3">المخزن</th><th className="p-3">التاريخ</th><th className="p-3">الإجمالي</th><th className="p-3">الحالة</th></tr></thead><tbody>{orders.map(o => <tr key={o.id} className="border-b last:border-0"><td className="p-3 font-medium">{o.order_number}</td><td className="p-3">{o.customer_id}</td><td className="p-3">{o.warehouse_id}</td><td className="p-3">{o.order_date}</td><td className="p-3">{o.total_amount}</td><td className="p-3">{o.status}</td></tr>)}</tbody></table></div>
  </section>;
}
