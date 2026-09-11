import { useEffect, useState } from "react";

interface Customer { id: number; code: string; name: string; tax_id?: string | null; phone?: string | null; email?: string | null; credit_limit: string; is_active: boolean; }

export default function CustomersPage() {
  const [companyId, setCompanyId] = useState("1");
  const [customers, setCustomers] = useState<Customer[]>([]);
  const load = () => fetch(`/api/v1/customers?company_id=${encodeURIComponent(companyId)}`).then(r => r.ok ? r.json() : []).then(setCustomers).catch(() => setCustomers([]));
  useEffect(load, [companyId]);
  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">العملاء</h1><p className="mt-1 text-sm text-muted-foreground">دليل العملاء الموحد للشركة، كأساس للمبيعات والذمم المدينة.</p></header>
    <div className="flex gap-3"><input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={e => setCompanyId(e.target.value)} placeholder="Company ID" /><button className="rounded-lg border px-4 py-2" onClick={load}>تحديث</button></div>
    <div className="overflow-hidden rounded-2xl border bg-card"><table className="w-full text-right text-sm"><thead><tr className="border-b"><th className="p-3">الكود</th><th className="p-3">العميل</th><th className="p-3">الهاتف</th><th className="p-3">البريد</th><th className="p-3">الحد الائتماني</th><th className="p-3">الحالة</th></tr></thead><tbody>{customers.map(c => <tr key={c.id} className="border-b last:border-0"><td className="p-3">{c.code}</td><td className="p-3 font-medium">{c.name}</td><td className="p-3">{c.phone || "—"}</td><td className="p-3">{c.email || "—"}</td><td className="p-3">{c.credit_limit}</td><td className="p-3">{c.is_active ? "نشط" : "موقوف"}</td></tr>)}</tbody></table></div>
  </section>;
}
