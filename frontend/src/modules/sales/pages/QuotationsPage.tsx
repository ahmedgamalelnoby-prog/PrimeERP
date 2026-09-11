import { useEffect, useState } from "react";

interface Quotation { id: number; quotation_number: string; customer_id: number; quotation_date: string; valid_until?: string | null; status: string; total_amount: string; }

export default function QuotationsPage() {
  const [companyId, setCompanyId] = useState("1");
  const [rows, setRows] = useState<Quotation[]>([]);
  const load = () => fetch(`/api/v1/sales/quotations?company_id=${encodeURIComponent(companyId)}`).then(r => r.ok ? r.json() : []).then(setRows).catch(() => setRows([]));
  useEffect(load, [companyId]);
  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">عروض الأسعار</h1><p className="mt-1 text-sm text-muted-foreground">دورة العرض: مسودة → مرسل → مقبول أو مرفوض، ويمكن تحويل العرض المقبول إلى طلب مبيعات.</p></header>
    <div className="flex gap-3"><input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={e => setCompanyId(e.target.value)} placeholder="Company ID" /><button className="rounded-lg border px-4 py-2" onClick={load}>تحديث</button></div>
    <div className="overflow-hidden rounded-2xl border bg-card"><table className="w-full text-right text-sm"><thead><tr className="border-b"><th className="p-3">رقم العرض</th><th className="p-3">العميل</th><th className="p-3">التاريخ</th><th className="p-3">الصلاحية</th><th className="p-3">الإجمالي</th><th className="p-3">الحالة</th></tr></thead><tbody>{rows.map(q => <tr key={q.id} className="border-b last:border-0"><td className="p-3 font-medium">{q.quotation_number}</td><td className="p-3">{q.customer_id}</td><td className="p-3">{q.quotation_date}</td><td className="p-3">{q.valid_until ?? "—"}</td><td className="p-3">{q.total_amount}</td><td className="p-3">{q.status}</td></tr>)}</tbody></table></div>
  </section>;
}
