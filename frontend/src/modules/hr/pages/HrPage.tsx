import { FormEvent, useCallback, useEffect, useState } from "react";
import client from "@/shared/api/client";

type Employee = { id: number; employee_no: string; name: string; is_active: boolean };
type LeaveRequest = {
  id: number; employee_id: number; leave_type: string; start_date: string; end_date: string;
  requested_days: string | number; reason?: string | null; status: string;
  submitted_by_user_id: number; decision_reason?: string | null;
};
type LeaveBalance = {
  id: number; employee_id: number; leave_type: string;
  entitled_days: string | number; consumed_days: string | number; available_days: string | number;
};
const selectedCompany = () => {
  const id = Number(localStorage.getItem("company_id"));
  return Number.isInteger(id) && id > 0 ? id : null;
};
const today = () => new Date().toISOString().slice(0, 10);

export default function HrPage() {
  const companyId = selectedCompany();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [balances, setBalances] = useState<LeaveBalance[]>([]);
  const [workforce, setWorkforce] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [employeeForm, setEmployeeForm] = useState({ employee_no: "", name: "", hire_date: today(), basic_salary: "0" });
  const [balanceForm, setBalanceForm] = useState({ employee_id: "", leave_type: "annual", entitled_days: "0" });
  const [leaveForm, setLeaveForm] = useState({
    employee_id: "", leave_type: "annual", start_date: today(), end_date: today(), requested_days: "1", reason: "",
  });

  const load = useCallback(async () => {
    if (!companyId) {
      setError("اختر شركة فعالة أولاً.");
      return;
    }
    setError("");
    try {
      const [employeeResponse, requestResponse, balanceResponse, workforceResponse] = await Promise.all([
        client.get("/enterprise/employees", { params: { company_id: companyId } }),
        client.get("/hr/leave-requests", { params: { company_id: companyId } }),
        client.get("/hr/leave-balances", { params: { company_id: companyId } }),
        client.get("/hr/workforce", { params: { company_id: companyId } }),
      ]);
      setEmployees(Array.isArray(employeeResponse.data) ? employeeResponse.data : []);
      setRequests(Array.isArray(requestResponse.data) ? requestResponse.data : []);
      setBalances(Array.isArray(balanceResponse.data) ? balanceResponse.data : []);
      setWorkforce(Array.isArray(workforceResponse.data) ? workforceResponse.data : []);
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل بيانات الموارد البشرية.");
    }
  }, [companyId]);

  useEffect(() => { void load(); }, [load]);

  async function submitEmployee(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post("/enterprise/employees", { ...employeeForm, company_id: companyId, basic_salary: Number(employeeForm.basic_salary) });
      setEmployeeForm({ employee_no: "", name: "", hire_date: today(), basic_salary: "0" });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر إضافة الموظف."); }
    finally { setBusy(false); }
  }

  async function saveBalance(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.put("/hr/leave-balances", {
        employee_id: Number(balanceForm.employee_id),
        leave_type: balanceForm.leave_type,
        entitled_days: Number(balanceForm.entitled_days),
      }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر حفظ رصيد الإجازة."); }
    finally { setBusy(false); }
  }

  async function submitLeave(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post("/hr/leave-requests", {
        ...leaveForm,
        employee_id: Number(leaveForm.employee_id),
        requested_days: Number(leaveForm.requested_days),
        reason: leaveForm.reason || null,
      }, { params: { company_id: companyId } });
      setLeaveForm({ ...leaveForm, reason: "" });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر إرسال طلب الإجازة."); }
    finally { setBusy(false); }
  }

  async function decide(requestId: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/leave-requests/${requestId}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر اتخاذ قرار الإجازة."); }
    finally { setBusy(false); }
  }

  const employeeName = (employeeId: number) => employees.find((employee) => employee.id === employeeId)?.name || `#${employeeId}`;
  const fieldClass = "w-full rounded-lg border bg-background px-3 py-2";
  const leaveTypeLabel: Record<string, string> = { annual: "سنوية", sick: "مرضية", unpaid: "بدون أجر", other: "أخرى" };

  return <section className="space-y-6 p-6" dir="rtl">
    <header>
      <h1 className="text-2xl font-bold">الموارد البشرية</h1>
      <p className="mt-1 text-sm text-muted-foreground">ملفات الموظفين، أرصدة الإجازات، ودورة اعتماد الطلبات.</p>
    </header>
    {error && <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error}</div>}

    <div className="grid gap-6 xl:grid-cols-3">
      <form onSubmit={submitEmployee} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">إضافة موظف</h2>
        <input required value={employeeForm.employee_no} onChange={e => setEmployeeForm({ ...employeeForm, employee_no: e.target.value })} placeholder="الرقم الوظيفي" className={fieldClass} />
        <input required value={employeeForm.name} onChange={e => setEmployeeForm({ ...employeeForm, name: e.target.value })} placeholder="اسم الموظف" className={fieldClass} />
        <input required type="date" value={employeeForm.hire_date} onChange={e => setEmployeeForm({ ...employeeForm, hire_date: e.target.value })} className={fieldClass} />
        <input required type="number" min="0" step="0.01" value={employeeForm.basic_salary} onChange={e => setEmployeeForm({ ...employeeForm, basic_salary: e.target.value })} placeholder="الراتب الأساسي" className={fieldClass} />
        <button disabled={busy || !companyId} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">حفظ الموظف</button>
      </form>

      <form onSubmit={saveBalance} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">إعداد رصيد إجازة</h2>
        <select required value={balanceForm.employee_id} onChange={e => setBalanceForm({ ...balanceForm, employee_id: e.target.value })} className={fieldClass}>
          <option value="">الموظف</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
        </select>
        <select value={balanceForm.leave_type} onChange={e => setBalanceForm({ ...balanceForm, leave_type: e.target.value })} className={fieldClass}>
          <option value="annual">سنوية</option><option value="sick">مرضية</option><option value="other">أخرى</option>
        </select>
        <input required type="number" min="0" step="0.01" value={balanceForm.entitled_days} onChange={e => setBalanceForm({ ...balanceForm, entitled_days: e.target.value })} placeholder="الرصيد المستحق بالأيام" className={fieldClass} />
        <button disabled={busy || !companyId || !employees.length} className="w-full rounded-lg border px-4 py-2 disabled:opacity-50">حفظ الرصيد</button>
      </form>

      <form onSubmit={submitLeave} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">طلب إجازة</h2>
        <select required value={leaveForm.employee_id} onChange={e => setLeaveForm({ ...leaveForm, employee_id: e.target.value })} className={fieldClass}>
          <option value="">الموظف</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
        </select>
        <select value={leaveForm.leave_type} onChange={e => setLeaveForm({ ...leaveForm, leave_type: e.target.value })} className={fieldClass}>
          <option value="annual">سنوية</option><option value="sick">مرضية</option><option value="unpaid">بدون أجر</option><option value="other">أخرى</option>
        </select>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs">من<input required type="date" value={leaveForm.start_date} onChange={e => setLeaveForm({ ...leaveForm, start_date: e.target.value })} className={fieldClass} /></label>
          <label className="text-xs">إلى<input required type="date" value={leaveForm.end_date} onChange={e => setLeaveForm({ ...leaveForm, end_date: e.target.value })} className={fieldClass} /></label>
        </div>
        <input required type="number" min="0.01" step="0.01" value={leaveForm.requested_days} onChange={e => setLeaveForm({ ...leaveForm, requested_days: e.target.value })} placeholder="عدد الأيام" className={fieldClass} />
        <textarea value={leaveForm.reason} onChange={e => setLeaveForm({ ...leaveForm, reason: e.target.value })} placeholder="السبب (اختياري)" className={fieldClass} />
        <button disabled={busy || !companyId || !employees.length} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">إرسال الطلب</button>
      </form>
    </div>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">أرصدة الإجازات</h2>
      {balances.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد أرصدة مسجلة.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">الموظف</th><th className="p-2 text-right">النوع</th><th className="p-2 text-right">المستحق</th><th className="p-2 text-right">المستخدم</th><th className="p-2 text-right">المتاح</th></tr></thead><tbody>{balances.map(balance => <tr key={balance.id} className="border-b"><td className="p-2">{employeeName(balance.employee_id)}</td><td className="p-2">{leaveTypeLabel[balance.leave_type] || balance.leave_type}</td><td className="p-2">{balance.entitled_days}</td><td className="p-2">{balance.consumed_days}</td><td className="p-2">{balance.available_days}</td></tr>)}</tbody></table></div>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <div className="flex items-center justify-between"><h2 className="font-semibold">طلبات الإجازة</h2><button type="button" onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">تحديث</button></div>
      {requests.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد طلبات.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">الموظف</th><th className="p-2 text-right">النوع</th><th className="p-2 text-right">الفترة</th><th className="p-2 text-right">الأيام</th><th className="p-2 text-right">الحالة</th><th className="p-2 text-right">السبب</th><th className="p-2 text-right">الإجراء</th></tr></thead><tbody>{requests.map(request => <tr key={request.id} className="border-b"><td className="p-2">{employeeName(request.employee_id)}</td><td className="p-2">{leaveTypeLabel[request.leave_type] || request.leave_type}</td><td className="p-2">{request.start_date} → {request.end_date}</td><td className="p-2">{request.requested_days}</td><td className="p-2">{request.status}</td><td className="max-w-48 truncate p-2" title={request.reason || ""}>{request.reason || "—"}</td><td className="p-2">{request.status === "pending" ? <div className="flex gap-2"><button disabled={busy} onClick={() => void decide(request.id, "approve")} className="rounded border px-2 py-1">موافقة</button><button disabled={busy} onClick={() => void decide(request.id, "reject")} className="rounded border px-2 py-1 text-destructive">رفض</button></div> : request.decision_reason || "—"}</td></tr>)}</tbody></table></div>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">ملفات مستخدمي الشركة</h2>
      {workforce.length === 0 ? <p className="text-sm text-muted-foreground">لا يوجد مستخدمون مسجلون.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">المستخدم</th><th className="p-2 text-right">الاسم</th><th className="p-2 text-right">الهاتف</th></tr></thead><tbody>{workforce.map((user:any) => <tr key={user.id} className="border-b"><td className="p-2">{user.username}</td><td className="p-2">{user.full_name || "—"}</td><td className="p-2">{user.phone || "—"}</td></tr>)}</tbody></table></div>}
    </section>
  </section>;
}
