import { useEffect, useState } from "react";
import client from "@/shared/api/client";

type Account = { id: number; code: string; name: string; name_ar?: string | null; statement?: string | null; normal_balance?: string | null };

export default function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const companyId = Number(localStorage.getItem("company_id")) || 0;

  useEffect(() => {
    if (!companyId) {
      setAccounts([]);
      setError("اختر شركة فعالة أولاً.");
      setLoading(false);
      return;
    }
    client.get<Account[]>("/chart-of-accounts/natural-accounts", { params: { company_id: companyId } })
      .then((response) => setAccounts(response.data))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "تعذر تحميل دليل الحسابات"))
      .finally(() => setLoading(false));
  }, [companyId]);

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">دليل الحسابات</h1>
        <p className="mt-1 text-sm text-muted-foreground">الحسابات الطبيعية المستخدمة في الدورة المحاسبية.</p>
      </header>
      {loading && <div className="rounded-xl border p-6">جاري التحميل...</div>}
      {error && <div className="rounded-xl border p-6 text-destructive">{error}</div>}
      {!loading && !error && (
        <div className="overflow-hidden rounded-2xl border bg-card">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40"><tr><th className="p-3 text-right">الكود</th><th className="p-3 text-right">الحساب</th><th className="p-3 text-right">القائمة</th><th className="p-3 text-right">الرصيد الطبيعي</th></tr></thead>
            <tbody>{accounts.map((account) => <tr key={account.id} className="border-b last:border-0"><td className="p-3 font-mono">{account.code}</td><td className="p-3 font-medium">{account.name_ar || account.name}</td><td className="p-3">{account.statement || "—"}</td><td className="p-3">{account.normal_balance || "—"}</td></tr>)}</tbody>
          </table>
          {accounts.length === 0 && <div className="p-6 text-muted-foreground">لا توجد حسابات متاحة.</div>}
        </div>
      )}
    </section>
  );
}
