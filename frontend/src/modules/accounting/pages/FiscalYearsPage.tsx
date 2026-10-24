import { useEffect, useMemo, useState } from "react";
import client from "@/shared/api/client";
import { formatCompanyDate, useCompanyClockDate, useCompanyDateFormat } from "@/utils/format-date";

function getStoredCompanyId(): number {
  try {
    const value = Number(localStorage.getItem("company_id"));
    return Number.isInteger(value) && value > 0 ? value : 0;
  } catch {
    return 0;
  }
}

type Period = {
  id: number;
  fiscal_year_id: number;
  period_number: number;
  code: string;
  name_ar: string;
  name_en: string;
  start_date: string;
  end_date: string;
  status: string;
  allow_posting: boolean;
};

type FiscalYear = {
  id: number;
  code: string;
  name_ar: string;
  name_en: string;
  start_date: string;
  end_date: string;
  status: string;
  is_current: boolean;
  periods: Period[];
};

export default function FiscalYearsPage() {
  const companyId = getStoredCompanyId();
  const dateFormat = useCompanyDateFormat(companyId);
  const { companyDate, error: clockError } = useCompanyClockDate(companyId);
  const [rows, setRows] = useState<FiscalYear[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    code: "",
    name_ar: "",
    name_en: "",
    start_date: "",
    end_date: "",
    create_monthly_periods: true,
    adjustment_period: false,
  });

  const load = async () => {
    if (!companyId) {
      setError("اختر شركة فعالة أولاً.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const response = await client.get("/accounting/fiscal-years", { params: { company_id: companyId } });
      setRows(Array.isArray(response.data) ? response.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل السنوات المالية");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void load(); }, [companyId]);

  // Seed fiscal-year defaults from the company server clock, never the device clock.
  useEffect(() => {
    if (!companyDate) return;
    const year = companyDate.slice(0, 4);
    setForm(current => ({
      ...current,
      code: current.code || year,
      name_ar: current.name_ar || `السنة المالية ${year}`,
      name_en: current.name_en || `Fiscal Year ${year}`,
      start_date: current.start_date || `${year}-01-01`,
      end_date: current.end_date || `${year}-12-31`,
    }));
  }, [companyDate]);

  const action = async (path: string, id: number) => {
    setBusy(id);
    setError("");
    try {
      await client.post(path);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تنفيذ العملية");
    } finally {
      setBusy(null);
    }
  };

  const createYear = async () => {
    setBusy(-1);
    setError("");
    try {
      await client.post("/accounting/fiscal-years", { company_id: companyId, ...form });
      setShowCreate(false);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر إنشاء السنة المالية");
    } finally {
      setBusy(null);
    }
  };

  const totals = useMemo(() => ({
    years: rows.length,
    open: rows.filter((x) => x.status === "open").length,
    periods: rows.reduce((sum, x) => sum + x.periods.length, 0),
  }), [rows]);

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold">السنوات والفترات المالية</h1>
          <p className="mt-1 text-sm text-muted-foreground">إدارة دورة السنة المالية والفترات وقابلية الترحيل للشركة الحالية.</p>
        </div>
        <button className="rounded-xl bg-primary px-4 py-2 text-primary-foreground" onClick={() => setShowCreate((v) => !v)} disabled={!companyId}>
          {showCreate ? "إلغاء" : "سنة مالية جديدة"}
        </button>
      </header>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border bg-card p-4"><div className="text-sm text-muted-foreground">إجمالي السنوات</div><div className="mt-1 text-2xl font-bold">{totals.years}</div></div>
        <div className="rounded-2xl border bg-card p-4"><div className="text-sm text-muted-foreground">السنوات المفتوحة</div><div className="mt-1 text-2xl font-bold">{totals.open}</div></div>
        <div className="rounded-2xl border bg-card p-4"><div className="text-sm text-muted-foreground">إجمالي الفترات</div><div className="mt-1 text-2xl font-bold">{totals.periods}</div></div>
      </div>

      {showCreate && (
        <section className="rounded-2xl border bg-card p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold">إنشاء سنة مالية</h2>
          <div className="grid gap-3 md:grid-cols-2">
            {(["code", "name_ar", "name_en", "start_date", "end_date"] as const).map((key) => (
              <label key={key} className="space-y-1 text-sm">
                <span>{key === "code" ? "الكود" : key === "name_ar" ? "الاسم بالعربية" : key === "name_en" ? "الاسم بالإنجليزية" : key === "start_date" ? "تاريخ البداية" : "تاريخ النهاية"}</span>
                <input
                  type={key.includes("date") ? "date" : "text"}
                  value={form[key]}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="w-full rounded-xl border bg-background px-3 py-2"
                />
              </label>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-4 text-sm">
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.create_monthly_periods} onChange={(e) => setForm({ ...form, create_monthly_periods: e.target.checked })} /> إنشاء الفترات الشهرية</label>
            <label className="flex items-center gap-2"><input type="checkbox" checked={form.adjustment_period} onChange={(e) => setForm({ ...form, adjustment_period: e.target.checked })} /> فترة تسويات</label>
          </div>
          <button className="mt-4 rounded-xl bg-primary px-4 py-2 text-primary-foreground" onClick={() => void createYear()} disabled={busy === -1}>
            {busy === -1 ? "جاري الإنشاء..." : "إنشاء"}
          </button>
        </section>
      )}

      {(error || clockError) && <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">{error || clockError}</div>}

      {loading ? <div className="rounded-xl border p-6">جاري التحميل...</div> : (
        <div className="space-y-4">
          {rows.map((year) => (
            <section key={year.id} className="overflow-hidden rounded-2xl border bg-card shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b p-4">
                <div>
                  <div className="flex items-center gap-2 font-semibold">{year.name_ar} <span className="text-xs text-muted-foreground">({year.code})</span></div>
                  <div className="mt-1 text-sm text-muted-foreground">{formatCompanyDate(year.start_date, dateFormat)} → {formatCompanyDate(year.end_date, dateFormat)} · {year.status}{year.is_current ? " · الحالية" : ""}</div>
                </div>
                <div className="flex flex-wrap gap-2">
                  {year.status === "draft" && <button className="rounded-lg border px-3 py-2 text-sm" disabled={busy === year.id} onClick={() => void action(`/accounting/fiscal-years/${year.id}/open`, year.id)}>فتح السنة</button>}
                  {year.status === "open" && <button className="rounded-lg border px-3 py-2 text-sm" disabled={busy === year.id} onClick={() => void action(`/accounting/fiscal-years/${year.id}/close`, year.id)}>إغلاق السنة</button>}
                </div>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px] text-sm">
                  <thead className="border-b bg-muted/30"><tr><th className="p-3 text-right">الفترة</th><th className="p-3 text-right">البداية</th><th className="p-3 text-right">النهاية</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">الترحيل</th><th className="p-3 text-right">إجراء</th></tr></thead>
                  <tbody>
                    {year.periods.map((period) => (
                      <tr key={period.id} className="border-b last:border-0">
                        <td className="p-3">{period.name_ar} ({period.code})</td>
                        <td className="p-3">{formatCompanyDate(period.start_date, dateFormat)}</td>
                        <td className="p-3">{formatCompanyDate(period.end_date, dateFormat)}</td>
                        <td className="p-3">{period.status}</td>
                        <td className="p-3">{period.allow_posting ? "مسموح" : "مغلق"}</td>
                        <td className="p-3">
                          {period.status === "open" && <button className="rounded-lg border px-3 py-1.5" disabled={busy === period.id} onClick={() => void action(`/accounting/fiscal-years/periods/${period.id}/close`, period.id)}>إغلاق</button>}
                          {period.status === "closed" && year.status === "open" && <button className="rounded-lg border px-3 py-1.5" disabled={busy === period.id} onClick={() => void action(`/accounting/fiscal-years/periods/${period.id}/reopen`, period.id)}>إعادة فتح</button>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!year.periods.length && <div className="p-5 text-sm text-muted-foreground">لا توجد فترات. أضف الفترات قبل فتح السنة.</div>}
              </div>
            </section>
          ))}
          {!rows.length && <div className="rounded-2xl border p-8 text-center text-muted-foreground">لا توجد سنوات مالية.</div>}
        </div>
      )}
    </section>
  );
}
