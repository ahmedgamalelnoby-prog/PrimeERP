import { FormEvent, useEffect, useState } from "react";
import client from "@/shared/api/client";
import { formatCompanyDate, useCompanyDateFormat } from "@/utils/format-date";

type Cheque = {
  id: number;
  cheque_number: string;
  bank_name?: string | null;
  due_date: string;
  amount: string | number;
  currency: string;
  status: string;
  direction: string;
};

const cid = () => {
  const n = Number(localStorage.getItem("company_id"));
  return Number.isInteger(n) && n > 0 ? n : null;
};

const terminal = ["withdrawn", "cancelled", "reversed"];
const receivedStatuses = ["received", "deposited", "under_collection", "returned", "resubmitted", "collected"];
const issuedStatuses = ["issued", "cleared"];

export default function TreasuryPage() {
  const companyId = cid();
  const dateFormat = useCompanyDateFormat(companyId);
  const [rows, setRows] = useState<Cheque[]>([]);
  const [withdrawableIds, setWithdrawableIds] = useState<Set<number>>(new Set());
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [direction, setDirection] = useState<"received" | "issued">("received");
  const [partnerId, setPartnerId] = useState("");
  const [number, setNumber] = useState("");
  const [bank, setBank] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [due, setDue] = useState(new Date().toISOString().slice(0, 10));
  const [amount, setAmount] = useState("");
  const [saving, setSaving] = useState(false);

  async function load() {
    setLoading(true);
    if (!companyId) {
      setRows([]);
      setWithdrawableIds(new Set());
      setError("اختر شركة فعالة أولاً.");
      setLoading(false);
      return;
    }
    try {
      const [all, withdrawable] = await Promise.all([
        client.get("/treasury/cheques", { params: { company_id: companyId } }),
        client.get("/treasury/cheques/withdrawable", { params: { company_id: companyId } }),
      ]);
      setRows(Array.isArray(all.data) ? all.data : []);
      setWithdrawableIds(new Set(
        (Array.isArray(withdrawable.data) ? withdrawable.data : [])
          .map((item: Cheque) => Number(item.id))
          .filter((id: number) => Number.isInteger(id) && id > 0),
      ));
      setError("");
    } catch (e: any) {
      setRows([]);
      setWithdrawableIds(new Set());
      setError(e?.response?.data?.detail || "تعذر تحميل الشيكات");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void load(); }, [companyId]);

  async function create(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    if (!Number(partnerId) || Number(partnerId) <= 0) {
      setError("يجب إدخال رقم الطرف المرتبط بالشيك.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      await client.post("/treasury/cheques", {
        company_id: companyId,
        partner_id: Number(partnerId),
        direction,
        cheque_number: number,
        bank_name: bank || null,
        cheque_date: date,
        due_date: due,
        amount: Number(amount),
        currency: "EGP",
      });
      setNumber("");
      setBank("");
      setPartnerId("");
      setAmount("");
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر إنشاء الشيك");
    } finally {
      setSaving(false);
    }
  }

  async function action(id: number, kind: string) {
    if (!companyId) return;
    try {
      await client.post("/treasury/cheques/" + id + "/" + kind, { company_id: companyId });
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تنفيذ العملية");
    }
  }

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">الخزينة والبنوك والشيكات</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          إدارة الشيكات المستلمة والصادرة مع دورة الإيداع والتحصيل والإرجاع وإعادة التقديم والسحب والعكس.
        </p>
      </header>

      {error && <div className="rounded-xl border bg-destructive/10 p-3 text-sm">{error}</div>}

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <form onSubmit={create} className="space-y-3 rounded-2xl border bg-card p-5 shadow-sm">
          <h2 className="font-semibold">{direction === "received" ? "إضافة شيك مستلم" : "إضافة شيك صادر"}</h2>
          <select value={direction} onChange={e => setDirection(e.target.value as "received" | "issued")} className="w-full rounded-lg border bg-background px-3 py-2">
            <option value="received">مستلم</option>
            <option value="issued">صادر</option>
          </select>
          <input required type="number" min="1" value={partnerId} onChange={e => setPartnerId(e.target.value)} placeholder="رقم الطرف" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required value={number} onChange={e => setNumber(e.target.value)} placeholder="رقم الشيك" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input value={bank} onChange={e => setBank(e.target.value)} placeholder="البنك" className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required type="date" value={date} onChange={e => setDate(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required type="date" value={due} onChange={e => setDue(e.target.value)} className="w-full rounded-lg border bg-background px-3 py-2" />
          <input required type="number" min="0.01" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="المبلغ EGP" className="w-full rounded-lg border bg-background px-3 py-2" />
          <button disabled={saving || !companyId || Number(amount) <= 0 || !number.trim()} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">
            {saving ? "جارٍ الحفظ..." : "حفظ الشيك"}
          </button>
        </form>

        <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
          <div className="flex items-center justify-between border-b p-4">
            <h2 className="font-semibold">الشيكات</h2>
            <button onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button>
          </div>
          {loading ? <div className="p-8 text-center text-sm">جارٍ التحميل...</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-muted-foreground">لا توجد شيكات.</div> :
            <div className="overflow-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b bg-muted/40">
                  <th className="p-3 text-right">الاتجاه</th><th className="p-3 text-right">الرقم</th><th className="p-3 text-right">البنك</th>
                  <th className="p-3 text-right">المبلغ</th><th className="p-3 text-right">الاستحقاق</th><th className="p-3 text-right">الحالة</th><th className="p-3 text-right">إجراء</th>
                </tr></thead>
                <tbody>{rows.map(c => <tr key={c.id} className="border-b">
                  <td className="p-3">{c.direction === "received" ? "مستلم" : "صادر"}</td>
                  <td className="p-3">{c.cheque_number}</td><td className="p-3">{c.bank_name || "—"}</td>
                  <td className="p-3">{c.amount} {c.currency}</td><td className="p-3">{formatCompanyDate(c.due_date, dateFormat)}</td><td className="p-3">{c.status}</td>
                  <td className="p-3"><div className="flex flex-wrap gap-1">
                    {c.status === "received" && <button onClick={() => void action(c.id, "deposit")} className="rounded border px-2 py-1 text-xs">إيداع</button>}
                    {c.status === "deposited" && <button onClick={() => void action(c.id, "under-collection")} className="rounded border px-2 py-1 text-xs">تحت التحصيل</button>}
                    {["deposited", "under_collection", "resubmitted"].includes(c.status) && <button onClick={() => void action(c.id, "collect")} className="rounded border px-2 py-1 text-xs">تحصيل</button>}
                    {c.status === "resubmitted" && <button onClick={() => void action(c.id, "under-collection")} className="rounded border px-2 py-1 text-xs">تحت التحصيل</button>}
                    {receivedStatuses.includes(c.status) && !["collected", "returned"].includes(c.status) && <button onClick={() => void action(c.id, "return")} className="rounded border px-2 py-1 text-xs">مرتجع</button>}
                    {c.status === "returned" && <button onClick={() => void action(c.id, "resubmit")} className="rounded border px-2 py-1 text-xs">إعادة تقديم</button>}
                    {c.status === "issued" && <button onClick={() => void action(c.id, "collect")} className="rounded border px-2 py-1 text-xs">تسوية</button>}
                    {issuedStatuses.includes(c.status) && <button onClick={() => void action(c.id, "reverse")} className="rounded border px-2 py-1 text-xs">عكس</button>}
                    {withdrawableIds.has(c.id) && !terminal.includes(c.status) && <button onClick={() => void action(c.id, "withdraw")} className="rounded border px-2 py-1 text-xs">سحب</button>}
                    {!terminal.includes(c.status) && c.status !== "cleared" && <button onClick={() => void action(c.id, "cancel")} className="rounded border px-2 py-1 text-xs">إلغاء</button>}
                    {c.status === "collected" && <button onClick={() => void action(c.id, "reverse")} className="rounded border px-2 py-1 text-xs">عكس</button>}
                  </div></td>
                </tr>)}</tbody>
              </table>
            </div>}
        </div>
      </div>
    </section>
  );
}
