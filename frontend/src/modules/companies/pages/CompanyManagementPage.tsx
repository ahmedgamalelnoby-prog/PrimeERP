import { FormEvent, useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import client from "@/shared/api/client";
import "@/shared/api/interceptors";
import { useAuth } from "@/modules/identity/hooks/useAuth";
import { storage } from "@/shared/utils/storage";

type Company = { id: number; tenant_id: number; name: string; code: string | null; email: string | null; tax_id: string | null; is_active: boolean };
type Branch = { id: number; tenant_id: number; company_id: number; name: string; code: string | null; email: string | null; is_active: boolean };
type Tenant = { id: number; name: string; slug: string; status: string; is_active: boolean };
type TenantList = { items: Tenant[]; total: number };

export default function CompanyManagementPage() {
  const branches = useLocation().pathname === "/branches";
  const { user } = useAuth();
  const isPlatformAdmin = Boolean(user?.is_platform_admin);
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [tenantId, setTenantId] = useState(() => storage.getTenantId() || "");
  const [companies, setCompanies] = useState<Company[]>([]);
  const [rows, setRows] = useState<(Company | Branch)[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadTenants = useCallback(async () => {
    const response = await client.get<TenantList>("/platform/tenants", { params: { page: 1, page_size: 100 } });
    const available = response.data.items.filter((tenant) => tenant.is_active);
    setTenants(available);
    const stored = storage.getTenantId();
    if (stored && !available.some((tenant) => String(tenant.id) === stored)) {
      storage.setTenantId(null);
      setTenantId("");
    }
  }, []);

  const loadCompanies = useCallback(async () => {
    const response = await client.get<Company[]>("/companies?active_only=true");
    setCompanies(response.data);
    setCompanyId((current) => response.data.some((company) => String(company.id) === current) ? current : "");
  }, []);

  const loadRows = useCallback(async () => {
    if (isPlatformAdmin && !tenantId) {
      setCompanies([]);
      setRows([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      await loadCompanies();
      if (branches) {
        if (!companyId) {
          setRows([]);
        } else {
          const response = await client.get<Branch[]>("/branches", { params: { company_id: Number(companyId) } });
          setRows(response.data);
        }
      } else {
        const response = await client.get<Company[]>("/companies");
        setRows(response.data);
      }
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || "تعذر تحميل البيانات");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [branches, companyId, isPlatformAdmin, loadCompanies, tenantId]);

  useEffect(() => {
    if (!user) return;
    if (isPlatformAdmin) {
      void loadTenants().catch((requestError: any) => {
        setError(requestError?.response?.data?.detail || "تعذر تحميل قائمة الـ Tenants");
        setLoading(false);
      });
    } else {
      storage.setTenantId(user.tenant_id);
      setTenantId(user.tenant_id ? String(user.tenant_id) : "");
    }
  }, [user, isPlatformAdmin, loadTenants]);

  useEffect(() => {
    if (!user || (isPlatformAdmin && !tenantId)) {
      setCompanies([]);
      setRows([]);
      setLoading(false);
      return;
    }
    void loadRows();
  }, [user, isPlatformAdmin, tenantId, companyId, branches, loadRows]);

  function selectTenant(value: string) {
    setTenantId(value);
    storage.setTenantId(value ? Number(value) : null);
    localStorage.removeItem("company_id");
    setCompanyId("");
    setCompanies([]);
    setRows([]);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      if (isPlatformAdmin && !tenantId) throw new Error("اختر Tenant أولاً قبل إدارة الشركات.");
      if (branches) {
        if (!companyId) throw new Error("اختر الشركة أولاً");
        await client.post("/branches", { company_id: Number(companyId), name, code: code || null, email: email || null });
      } else {
        await client.post("/companies", { name, code: code || null, email: email || null });
      }
      setName("");
      setCode("");
      setEmail("");
      await loadRows();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || requestError?.message || "تعذر الحفظ");
    } finally {
      setSaving(false);
    }
  }

  async function deactivate(id: number) {
    if (!window.confirm("هل تريد تعطيل هذا السجل؟")) return;
    try {
      await client.delete(`${branches ? "/branches" : "/companies"}/${id}`);
      await loadRows();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || "تعذر التعطيل");
    }
  }

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">{branches ? "الفروع" : "الشركات"}</h1>
      <p className="mt-1 text-sm text-muted-foreground">إدارة فعلية مع عزل الـ tenant وعدم استخدام شركة افتراضية.</p>
    </header>

    {isPlatformAdmin && <div className="max-w-xl rounded-2xl border bg-card p-5">
      <label className="mb-2 block text-sm font-semibold">Tenant context (مطلوب لمسؤول المنصة)</label>
      <select value={tenantId} onChange={(event) => selectTenant(event.target.value)} className="w-full rounded-lg border bg-background px-3 py-2">
        <option value="">اختر الـ Tenant صراحةً</option>
        {tenants.map((tenant) => <option key={tenant.id} value={tenant.id}>{tenant.name} · {tenant.slug}</option>)}
      </select>
      {!tenantId && <p className="mt-2 text-sm text-amber-700">لن يتم تحميل أو إنشاء شركات قبل اختيار Tenant.</p>}
    </div>}

    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <form onSubmit={submit} className="space-y-4 rounded-2xl border bg-card p-5 shadow-sm">
        {branches && <select required value={companyId} onChange={(event) => { setCompanyId(event.target.value); if (event.target.value) localStorage.setItem("company_id", event.target.value); else localStorage.removeItem("company_id"); }} className="w-full rounded-lg border bg-background px-3 py-2">
          <option value="">اختر الشركة</option>{companies.map((company) => <option key={company.id} value={company.id}>{company.name} {company.code ? `(${company.code})` : ""}</option>)}
        </select>}
        <input required value={name} onChange={(event) => setName(event.target.value)} placeholder="الاسم" className="w-full rounded-lg border bg-background px-3 py-2" />
        <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="الكود" className="w-full rounded-lg border bg-background px-3 py-2" />
        <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="البريد الإلكتروني" className="w-full rounded-lg border bg-background px-3 py-2" />
        {error && <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}
        <button disabled={saving || (isPlatformAdmin && !tenantId) || (branches && !companyId)} className="w-full rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground disabled:opacity-50">{saving ? "جارٍ الحفظ..." : "إضافة"}</button>
      </form>
      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4"><h2 className="font-semibold">السجلات</h2><button type="button" onClick={() => void loadRows()} disabled={isPlatformAdmin && !tenantId} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
        {loading ? <div className="p-8 text-center text-sm">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">{isPlatformAdmin && !tenantId ? "اختر Tenant لعرض الشركات التابعة له." : "لا توجد سجلات."}</div> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40"><th className="p-3 text-right">الاسم</th><th className="p-3 text-right">الكود</th>{branches && <th className="p-3 text-right">الشركة</th>}<th className="p-3 text-right">البريد</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">إجراء</th></tr></thead><tbody>{rows.map((row) => <tr key={row.id} className="border-b last:border-0"><td className="p-3 font-medium">{row.name}</td><td className="p-3">{row.code || "—"}</td>{branches && <td className="p-3">{companies.find((company) => company.id === (row as Branch).company_id)?.name || (row as Branch).company_id}</td>}<td className="p-3">{row.email || "—"}</td><td className="p-3">{row.is_active ? "نشط" : "غير نشط"}</td><td className="p-3"><button type="button" onClick={() => void deactivate(row.id)} disabled={!row.is_active} className="rounded-lg border px-3 py-1 text-xs disabled:opacity-40">تعطيل</button></td></tr>)}</tbody></table></div>}
      </div>
    </div>
  </section>;
}
