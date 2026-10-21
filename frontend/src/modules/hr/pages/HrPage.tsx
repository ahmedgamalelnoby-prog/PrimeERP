import { FormEvent, useCallback, useEffect, useState } from "react";
import client from "@/shared/api/client";

type Employee = { id: number; employee_no: string; name: string; is_active: boolean };
type LeaveRequest = {
  id: number; employee_id: number; leave_type: string; start_date: string; end_date: string;
  requested_days: string | number; reason?: string | null; status: string;
  submitted_by_user_id: number; decision_reason?: string | null;
};
type Attendance = { id: number; employee_id: number; attendance_date: string; source: string; check_in_at: string; check_out_at?: string | null };
type OvertimeRequest = { id: number; attendance_record_id: number; requested_hours: string | number; reason: string; status: string };
type AttendanceCorrection = { id: number; attendance_record_id: number; proposed_check_in_at: string; proposed_check_out_at?: string | null; reason: string; status: string };
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
  const [attendance, setAttendance] = useState<Attendance[]>([]);
  const [corrections, setCorrections] = useState<AttendanceCorrection[]>([]);
  const [overtimeRequests, setOvertimeRequests] = useState<OvertimeRequest[]>([]);
  const [overtimeForm, setOvertimeForm] = useState({ attendance_record_id: "", requested_hours: "1", reason: "" });
  const [companyTimezone, setCompanyTimezone] = useState("Africa/Cairo");
  const [correctionTarget, setCorrectionTarget] = useState<number | null>(null);
  const [correctionForm, setCorrectionForm] = useState({ check_in_time: "", check_out_time: "", reason: "" });
  const [attendanceForm, setAttendanceForm] = useState({ employee_id: "", attendance_date: today(), check_in_time: today() + "T09:00", check_out_time: today() + "T17:00" });
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
      const [employeeResponse, requestResponse, balanceResponse, workforceResponse, attendanceResponse, correctionResponse, overtimeResponse] = await Promise.all([
        client.get("/enterprise/employees", { params: { company_id: companyId } }),
        client.get("/hr/leave-requests", { params: { company_id: companyId } }),
        client.get("/hr/leave-balances", { params: { company_id: companyId } }),
        client.get("/hr/workforce", { params: { company_id: companyId } }),
        client.get("/hr/attendance", { params: { company_id: companyId } }),
        client.get("/hr/attendance-corrections", { params: { company_id: companyId } }),
        client.get("/hr/overtime-requests", { params: { company_id: companyId } }),
      ]);
      setEmployees(Array.isArray(employeeResponse.data) ? employeeResponse.data : []);
      setRequests(Array.isArray(requestResponse.data) ? requestResponse.data : []);
      setBalances(Array.isArray(balanceResponse.data) ? balanceResponse.data : []);
      setWorkforce(Array.isArray(workforceResponse.data) ? workforceResponse.data : []);
      setAttendance(Array.isArray(attendanceResponse.data) ? attendanceResponse.data : []);
      setCorrections(Array.isArray(correctionResponse.data) ? correctionResponse.data : []);
      setOvertimeRequests(Array.isArray(overtimeResponse.data) ? overtimeResponse.data : []);
      try {
        const settingsResponse = await client.get("/company-settings", { params: { company_id: companyId } });
        const configuredTimezone = settingsResponse.data?.settings?.find((setting: { key?: string }) => setting.key === "general.timezone")?.value;
        setCompanyTimezone(typeof configuredTimezone === "string" && configuredTimezone ? configuredTimezone : "Africa/Cairo");
      } catch {
        setCompanyTimezone("Africa/Cairo");
      }
    } catch (e: any) {
      setError(e?.response?.data?.detail || "تعذر تحميل بيانات الموارد البشرية.");
    }
  }, [companyId]);

  useEffect(() => { void load(); }, [load]);

  function displayDateTime(value?: string | null) {
    if (!value) return "—";
    try { return new Intl.DateTimeFormat("ar-EG", { timeZone: companyTimezone, dateStyle: "short", timeStyle: "short" }).format(new Date(value)); }
    catch { return value; }
  }

  async function submitAttendance(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post("/hr/attendance", {
        employee_id: Number(attendanceForm.employee_id),
        attendance_date: attendanceForm.attendance_date,
        check_in_time: attendanceForm.check_in_time,
        check_out_time: attendanceForm.check_out_time || null,
      }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر تسجيل الحضور."); }
    finally { setBusy(false); }
  }

  function editCorrection(record: Attendance) {
    const localValue = (value?: string | null) => {
      if (!value) return "";
      const parts = new Intl.DateTimeFormat("en-CA", {
        timeZone: companyTimezone, year: "numeric", month: "2-digit", day: "2-digit",
        hour: "2-digit", minute: "2-digit", hourCycle: "h23",
      }).formatToParts(new Date(value));
      const part = (type: string) => parts.find(item => item.type === type)?.value || "";
      return `${part("year")}-${part("month")}-${part("day")}T${part("hour")}:${part("minute")}`;
    };
    setCorrectionTarget(record.id);
    setCorrectionForm({ check_in_time: localValue(record.check_in_at), check_out_time: localValue(record.check_out_at), reason: "" });
  }

  async function submitCorrection(e: FormEvent) {
    e.preventDefault();
    if (!companyId || correctionTarget === null) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/attendance/${correctionTarget}/corrections`, {
        check_in_time: correctionForm.check_in_time,
        check_out_time: correctionForm.check_out_time || null,
        reason: correctionForm.reason,
      }, { params: { company_id: companyId } });
      setCorrectionTarget(null);
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر إرسال تصحيح الحضور."); }
    finally { setBusy(false); }
  }

  async function submitOvertime(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post("/hr/overtime-requests", {
        attendance_record_id: Number(overtimeForm.attendance_record_id),
        requested_hours: Number(overtimeForm.requested_hours),
        reason: overtimeForm.reason,
      }, { params: { company_id: companyId } });
      setOvertimeForm({ ...overtimeForm, reason: "" });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر إرسال طلب الساعات الإضافية."); }
    finally { setBusy(false); }
  }

  async function decideOvertime(id: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/overtime-requests/${id}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر اتخاذ قرار الساعات الإضافية."); }
    finally { setBusy(false); }
  }

  async function decideCorrection(id: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/attendance-corrections/${id}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر اعتماد تصحيح الحضور."); }
    finally { setBusy(false); }
  }

  async function saveWorkforce(user: any) {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.patch(`/hr/workforce/${user.id}`, {
        full_name: user.full_name || null,
        phone: user.phone || null,
        address: user.address || null,
        preferred_language: user.preferred_language || "ar",
      }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "تعذر حفظ ملف المستخدم."); }
    finally { setBusy(false); }
  }

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

    <form onSubmit={submitAttendance} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-6">
      <h2 className="font-semibold md:col-span-6">تسجيل حضور يدوي</h2>
      <p className="text-xs text-muted-foreground md:col-span-6">الإدخال اليدوي متاح عندما يكون مصدر الحضور في إعدادات الشركة «يدوي». موصلات البصمة والموبايل لم تُربط بعد.</p>
      <select required value={attendanceForm.employee_id} onChange={e => setAttendanceForm({ ...attendanceForm, employee_id: e.target.value })} className={fieldClass}>
        <option value="">الموظف</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
      </select>
      <input required type="date" value={attendanceForm.attendance_date} onChange={e => setAttendanceForm({ ...attendanceForm, attendance_date: e.target.value })} className={fieldClass} />
      <label className="text-xs">حضور<input required type="datetime-local" value={attendanceForm.check_in_time} onChange={e => setAttendanceForm({ ...attendanceForm, check_in_time: e.target.value })} className={fieldClass} /></label>
      <label className="text-xs">انصراف<input type="datetime-local" value={attendanceForm.check_out_time} onChange={e => setAttendanceForm({ ...attendanceForm, check_out_time: e.target.value })} className={fieldClass} /></label>
      <button disabled={busy || !companyId || !employees.length} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">تسجيل</button>
    </form>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">سجل الحضور</h2>
      {attendance.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد سجلات حضور.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">الموظف</th><th className="p-2 text-right">التاريخ</th><th className="p-2 text-right">الحضور</th><th className="p-2 text-right">الانصراف</th><th className="p-2 text-right">المصدر</th><th className="p-2 text-right">إجراء</th></tr></thead><tbody>{attendance.map(record => <tr key={record.id} className="border-b"><td className="p-2">{employeeName(record.employee_id)}</td><td className="p-2">{record.attendance_date}</td><td className="p-2">{displayDateTime(record.check_in_at)}</td><td className="p-2">{displayDateTime(record.check_out_at)}</td><td className="p-2">{record.source}</td><td className="p-2"><button type="button" onClick={() => editCorrection(record)} className="rounded border px-2 py-1">طلب تصحيح</button></td></tr>)}</tbody></table></div>}
      {correctionTarget !== null && <form onSubmit={submitCorrection} className="grid gap-3 rounded-xl border p-4 md:grid-cols-4">
        <h3 className="font-medium md:col-span-4">تصحيح السجل #{correctionTarget}</h3>
        <label className="text-xs">وقت الحضور<input required type="datetime-local" value={correctionForm.check_in_time} onChange={e => setCorrectionForm({ ...correctionForm, check_in_time: e.target.value })} className={fieldClass} /></label>
        <label className="text-xs">وقت الانصراف<input type="datetime-local" value={correctionForm.check_out_time} onChange={e => setCorrectionForm({ ...correctionForm, check_out_time: e.target.value })} className={fieldClass} /></label>
        <input required value={correctionForm.reason} onChange={e => setCorrectionForm({ ...correctionForm, reason: e.target.value })} placeholder="سبب التصحيح" className={fieldClass} />
        <div className="flex gap-2"><button disabled={busy} className="rounded bg-primary px-3 py-2 text-primary-foreground">إرسال</button><button type="button" onClick={() => setCorrectionTarget(null)} className="rounded border px-3 py-2">إلغاء</button></div>
      </form>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">طلبات تصحيح الحضور</h2>
      {corrections.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد طلبات تصحيح.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">السجل</th><th className="p-2 text-right">الحضور المقترح</th><th className="p-2 text-right">الانصراف المقترح</th><th className="p-2 text-right">السبب</th><th className="p-2 text-right">الحالة</th><th className="p-2 text-right">قرار</th></tr></thead><tbody>{corrections.map(item => <tr key={item.id} className="border-b"><td className="p-2">#{item.attendance_record_id}</td><td className="p-2">{displayDateTime(item.proposed_check_in_at)}</td><td className="p-2">{displayDateTime(item.proposed_check_out_at)}</td><td className="p-2">{item.reason}</td><td className="p-2">{item.status}</td><td className="p-2">{item.status === "pending" ? <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => void decideCorrection(item.id, "approve")} className="rounded border px-2 py-1">موافقة</button><button type="button" disabled={busy} onClick={() => void decideCorrection(item.id, "reject")} className="rounded border px-2 py-1 text-destructive">رفض</button></div> : "—"}</td></tr>)}</tbody></table></div>}
    </section>

    <form onSubmit={submitOvertime} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-4">
      <h2 className="font-semibold md:col-span-4">طلب ساعات إضافية</h2>
      <p className="text-xs text-muted-foreground md:col-span-4">الحد المتاح يُحسب من وقت الحضور والانصراف مطروحًا منه ساعات العمل اليومية في إعدادات الشركة. الطلبات المنتظرة تُحجز حتى لا تتجاوز الطلبات إجمالي الساعات المسجلة.</p>
      <select required value={overtimeForm.attendance_record_id} onChange={e => setOvertimeForm({ ...overtimeForm, attendance_record_id: e.target.value })} className={fieldClass}>
        <option value="">سجل الحضور</option>{attendance.filter(record => record.check_out_at).map(record => <option key={record.id} value={record.id}>{employeeName(record.employee_id)} · {record.attendance_date}</option>)}
      </select>
      <input required type="number" min="0.01" step="0.01" value={overtimeForm.requested_hours} onChange={e => setOvertimeForm({ ...overtimeForm, requested_hours: e.target.value })} placeholder="الساعات" className={fieldClass} />
      <input required value={overtimeForm.reason} onChange={e => setOvertimeForm({ ...overtimeForm, reason: e.target.value })} placeholder="سبب العمل الإضافي" className={fieldClass} />
      <button disabled={busy || !companyId || !attendance.some(record => record.check_out_at)} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">إرسال الطلب</button>
    </form>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">طلبات الساعات الإضافية</h2>
      {overtimeRequests.length === 0 ? <p className="text-sm text-muted-foreground">لا توجد طلبات.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">الموظف</th><th className="p-2 text-right">التاريخ</th><th className="p-2 text-right">الساعات</th><th className="p-2 text-right">السبب</th><th className="p-2 text-right">الحالة</th><th className="p-2 text-right">القرار</th></tr></thead><tbody>{overtimeRequests.map(request => { const record = attendance.find(item => item.id === request.attendance_record_id); return <tr key={request.id} className="border-b"><td className="p-2">{record ? employeeName(record.employee_id) : "—"}</td><td className="p-2">{record?.attendance_date || "—"}</td><td className="p-2">{request.requested_hours}</td><td className="p-2">{request.reason}</td><td className="p-2">{request.status}</td><td className="p-2">{request.status === "pending" ? <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => void decideOvertime(request.id, "approve")} className="rounded border px-2 py-1">موافقة</button><button type="button" disabled={busy} onClick={() => void decideOvertime(request.id, "reject")} className="rounded border px-2 py-1 text-destructive">رفض</button></div> : "—"}</td></tr>; })}</tbody></table></div>}
    </section>

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
      {workforce.length === 0 ? <p className="text-sm text-muted-foreground">لا يوجد مستخدمون مسجلون.</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">المستخدم</th><th className="p-2 text-right">الاسم</th><th className="p-2 text-right">الهاتف</th><th className="p-2 text-right">العنوان</th><th className="p-2 text-right">إجراء</th></tr></thead><tbody>{workforce.map((user:any) => <tr key={user.id} className="border-b"><td className="p-2">{user.username}</td><td className="p-2"><input value={user.full_name || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, full_name: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><input value={user.phone || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, phone: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><input value={user.address || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, address: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><button disabled={busy} onClick={() => void saveWorkforce(user)} className="rounded border px-3 py-1">حفظ</button></td></tr>)}</tbody></table></div>}
    </section>
  </section>;
}
