import { FormEvent, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";

type Company = { id: number; tenant_id: number; name: string; code: string | null; email: string | null; tax_id: string | null; is_active: boolean };
type Branch = { id: number; tenant_id: number; company_id: number; name: string; code: string | null; email: string | null; is_active: boolean };

export default function CompanyManagementPage() {
  const branches = useLocation().pathname === "/branches";
  const [companies, setCompanies] = useState<Company[]>([]);
  const [rows, setRows] = useState<(Company | Branch)[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [name, setName] = useState(""); const [code, setCode] = useState(""); const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true); const [saving, setSaving] = useState(false); const [error, setError] = useState("");

  async function loadCompanies() {
    const r = await client.get<Company[]>("/companies?active_only=true");
    setCompanies(r.data); setCompanyId((current) => current || String(r.data[0]?.id || ""));
    if (!currentStorageCompany(r.data)) localStorage.removeItem("company_id");
    if (r.data.length) localStorage.setItem("company_id", String(Number(localStorage.getItem("company_id")) || r.data[0].id));
  }
  async function load() {
    setLoading(true); setError("");
    try {
      await loadCompanies();
      const r = branches ? await client.get<Branch[]>(`/branches?company_id=${companyId || localStorage.getItem("company_id") || ""}`) : await client.get<Company[]>("/companies");
      setRows(r.data);
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر تحميل البيانات"); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, [branches, companyId]);

  async function submit(e: FormEvent) {
    e.preventDefault(); setSaving(true); setError("");
    try {
      if (branches) {
        if (!companyId) throw new Error("اختر الشركة أولاً");
        await client.post("/branches", { company_id: Number(companyId), name, code: code || null, email: email || null });
      } else await client.post("/companies", { name, code: code || null, email: email || null });
      setName(""); setCode(""); setEmail(""); await load();
    } catch (e: any) { setError(e?.response?.data?.detail || e?.message || "تعذر الحفظ"); }
    finally { setSaving(false); }
  }
  async function deactivate(id: number) {
    if (!window.confirm("هل تريد تعطيل هذا السجل؟")) return;
    try { await client.delete(`${branches ? "/branches" : "/companies"}/${id}`); await load(); }
    catch (e: any) { setError(e?.response?.data?.detail || "تعذر التعطيل"); }
  }
  function currentStorageCompany(list: Company[]) { const id = Number(localStorage.getItem("company_id")); return list.some((c) => c.id === id); }

  return <section className="space-y-6 p-6" dir="rtl">
    <header><h1 className="text-2xl font-bold">{branches ? "الفروع" : "الشركات"}</h1><p className="mt-1 text-sm text-muted-foreground">إدارة فعلية مع عزل الـ tenant وعدم استخدام شركة افتراضية.</p></header>
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        {branches && <select required value={companyId} onChange={(e) => { setCompanyId(e.target.value); localStorage.setItem("company_id", e.target.value); }} className="w-full rounded-lg border bg-background px-3 py-2"><option value="">اختر الشركة</option>{companies.map(c => <option key={c.id} value={c.id}>{c.name} {c.code ? `(${c.code})` : ""}</option>)}</select>}
        <input required value={name} onChange={e => setName(e.target.value)} placeholder="الاسم" className="w-full rounded-lg border bg-background px-3 py-2" />
        <input value={code} onChange={e => setCode(e.target.value)} placeholder="الكود" className="w-full rounded-lg border bg-background px-3 py-2" />
        <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="البريد الإلكتروني" className="w-full rounded-lg border bg-background px-3 py-2" />
        {error && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button disabled={saving || (branches && !companyId)} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "إضافة"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm"><div className="flex items-center justify-between border-b p-4"><h2 className="font-semibold">السجلات</h2><button onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-8 text-center text-sm">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">لا توجد سجلات.</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40"><th className="p-3 text-right">الاسم</th><th className="p-3 text-right">الكود</th>{branches && <th className="p-3 text-right">الشركة</th>}<th className="p-3 text-right">البريد</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">إجراء</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id} className="border-b last:border-0"><td className="p-3 font-medium">{row.name}</td><td className="p-3">{row.code || "—"}</td>{branches && <td className="p-3">{companies.find(c => c.id === (row as Branch).company_id)?.name || (row as Branch).company_id}</td>}<td className="p-3">{row.email || "—"}</td><td className="p-3">{row.is_active ? "نشط" : "غير نشط"}</td><td className="p-3"><button onClick={() => void deactivate(row.id)} disabled={!row.is_active} className="rounded-lg border px-3 py-1 text-xs disabled:opacity-40">تعطيل</button></td></tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
