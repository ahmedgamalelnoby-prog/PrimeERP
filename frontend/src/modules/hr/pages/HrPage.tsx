import { FormEvent, useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import client from "@/shared/api/client";
import { formatCompanyDate, useCompanyClockDate, useCompanyDateFormat } from "@/utils/format-date";

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
  try {
    const id = Number(localStorage.getItem("company_id"));
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
};

export default function HrPage() {
  const { t, i18n } = useTranslation();
  const companyId = selectedCompany();
  const dateFormat = useCompanyDateFormat(companyId);
  const { companyDate, error: clockError } = useCompanyClockDate(companyId);
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
  const [attendanceForm, setAttendanceForm] = useState({ employee_id: "", attendance_date: "", check_in_time: "", check_out_time: "" });
  const [workforce, setWorkforce] = useState<any[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [employeeForm, setEmployeeForm] = useState({ employee_no: "", name: "", hire_date: "", basic_salary: "0" });
  const [balanceForm, setBalanceForm] = useState({ employee_id: "", leave_type: "annual", entitled_days: "0" });
  const [leaveForm, setLeaveForm] = useState({
    employee_id: "", leave_type: "annual", start_date: "", end_date: "", requested_days: "1", reason: "",
  });

  const load = useCallback(async () => {
    if (!companyId) {
      setError("{t("hr.activeCompanyRequired")}");
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
      setError(e?.response?.data?.detail || "{t("hr.loadFailed")}");
    }
  }, [companyId]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => { if (clockError) setError(clockError); }, [clockError]);
  useEffect(() => {
    if (!companyDate) return;
    setAttendanceForm(current => ({ ...current, attendance_date: current.attendance_date || companyDate, check_in_time: current.check_in_time || `${companyDate}T09:00`, check_out_time: current.check_out_time || `${companyDate}T17:00` }));
    setEmployeeForm(current => ({ ...current, hire_date: current.hire_date || companyDate }));
    setLeaveForm(current => ({ ...current, start_date: current.start_date || companyDate, end_date: current.end_date || companyDate }));
  }, [companyDate]);

  function displayDateTime(value?: string | null) {
    if (!value) return "—";
    try { return new Intl.DateTimeFormat(i18n.language.startsWith("ar") ? "ar-EG" : "en-US", { timeZone: companyTimezone, dateStyle: "short", timeStyle: "short" }).format(new Date(value)); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.attendanceFailed")}"); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.correctionSubmitFailed")}"); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.overtimeSubmitFailed")}"); }
    finally { setBusy(false); }
  }

  async function decideOvertime(id: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/overtime-requests/${id}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.overtimeDecisionFailed")}"); }
    finally { setBusy(false); }
  }

  async function decideCorrection(id: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/attendance-corrections/${id}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.correctionDecisionFailed")}"); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.saveWorkforceFailed")}"); }
    finally { setBusy(false); }
  }

  async function submitEmployee(e: FormEvent) {
    e.preventDefault();
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post("/enterprise/employees", { ...employeeForm, company_id: companyId, basic_salary: Number(employeeForm.basic_salary) });
      setEmployeeForm({ employee_no: "", name: "", hire_date: companyDate || "", basic_salary: "0" });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.addEmployeeFailed")}"); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.saveLeaveBalanceFailed")}"); }
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
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.leaveSubmitFailed")}"); }
    finally { setBusy(false); }
  }

  async function decide(requestId: number, decision: "approve" | "reject") {
    if (!companyId) return;
    setBusy(true); setError("");
    try {
      await client.post(`/hr/leave-requests/${requestId}/decision`, { decision }, { params: { company_id: companyId } });
      await load();
    } catch (e: any) { setError(e?.response?.data?.detail || "{t("hr.leaveDecisionFailed")}"); }
    finally { setBusy(false); }
  }

  const employeeName = (employeeId: number) => employees.find((employee) => employee.id === employeeId)?.name || `#${employeeId}`;
  const fieldClass = "w-full rounded-lg border bg-background px-3 py-2";
  const leaveTypeLabel: Record<string, string> = { annual: t("hr.leaveTypes.annual"), sick: t("hr.leaveTypes.sick"), unpaid: t("hr.leaveTypes.unpaid"), other: t("hr.leaveTypes.other") };

  return <section className="space-y-6 p-6" dir={i18n.dir()}>
    <header>
      <h1 className="text-2xl font-bold">{t("hr.title")}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t("hr.description")}</p>
    </header>
    {(error || clockError) && <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-sm">{error || clockError}</div>}

    <div className="grid gap-6 xl:grid-cols-3">
      <form onSubmit={submitEmployee} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">{t("hr.addEmployee")}</h2>
        <input required value={employeeForm.employee_no} onChange={e => setEmployeeForm({ ...employeeForm, employee_no: e.target.value })} placeholder="{t("hr.employeeNumber")}" className={fieldClass} />
        <input required value={employeeForm.name} onChange={e => setEmployeeForm({ ...employeeForm, name: e.target.value })} placeholder="{t("hr.employeeName")}" className={fieldClass} />
        <input required type="date" value={employeeForm.hire_date} onChange={e => setEmployeeForm({ ...employeeForm, hire_date: e.target.value })} className={fieldClass} />
        <input required type="number" min="0" step="0.01" value={employeeForm.basic_salary} onChange={e => setEmployeeForm({ ...employeeForm, basic_salary: e.target.value })} placeholder="{t("hr.basicSalary")}" className={fieldClass} />
        <button disabled={busy || !companyId} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{t("hr.saveEmployee")}</button>
      </form>

      <form onSubmit={saveBalance} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">{t("hr.setLeaveBalance")}</h2>
        <select required value={balanceForm.employee_id} onChange={e => setBalanceForm({ ...balanceForm, employee_id: e.target.value })} className={fieldClass}>
          <option value="">{t("hr.employee")}</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
        </select>
        <select value={balanceForm.leave_type} onChange={e => setBalanceForm({ ...balanceForm, leave_type: e.target.value })} className={fieldClass}>
          <option value="annual">{t("hr.leaveTypes.annual")}</option><option value="sick">{t("hr.leaveTypes.sick")}</option><option value="other">{t("hr.leaveTypes.other")}</option>
        </select>
        <input required type="number" min="0" step="0.01" value={balanceForm.entitled_days} onChange={e => setBalanceForm({ ...balanceForm, entitled_days: e.target.value })} placeholder="{t("hr.entitledDays")}" className={fieldClass} />
        <button disabled={busy || !companyId || !employees.length} className="w-full rounded-lg border px-4 py-2 disabled:opacity-50">{t("hr.saveBalance")}</button>
      </form>

      <form onSubmit={submitLeave} className="space-y-3 rounded-2xl border bg-card p-5">
        <h2 className="font-semibold">{t("hr.leaveRequest")}</h2>
        <select required value={leaveForm.employee_id} onChange={e => setLeaveForm({ ...leaveForm, employee_id: e.target.value })} className={fieldClass}>
          <option value="">{t("hr.employee")}</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
        </select>
        <select value={leaveForm.leave_type} onChange={e => setLeaveForm({ ...leaveForm, leave_type: e.target.value })} className={fieldClass}>
          <option value="annual">{t("hr.leaveTypes.annual")}</option><option value="sick">{t("hr.leaveTypes.sick")}</option><option value="unpaid">{t("hr.leaveTypes.unpaid")}</option><option value="other">{t("hr.leaveTypes.other")}</option>
        </select>
        <div className="grid grid-cols-2 gap-2">
          <label className="text-xs">{t("hr.from")}<input required type="date" value={leaveForm.start_date} onChange={e => setLeaveForm({ ...leaveForm, start_date: e.target.value })} className={fieldClass} /></label>
          <label className="text-xs">{t("hr.to")}<input required type="date" value={leaveForm.end_date} onChange={e => setLeaveForm({ ...leaveForm, end_date: e.target.value })} className={fieldClass} /></label>
        </div>
        <input required type="number" min="0.01" step="0.01" value={leaveForm.requested_days} onChange={e => setLeaveForm({ ...leaveForm, requested_days: e.target.value })} placeholder="{t("hr.daysCount")}" className={fieldClass} />
        <textarea value={leaveForm.reason} onChange={e => setLeaveForm({ ...leaveForm, reason: e.target.value })} placeholder="{t("hr.optionalReason")}" className={fieldClass} />
        <button disabled={busy || !companyId || !employees.length} className="w-full rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{t("hr.submitRequest")}</button>
      </form>
    </div>

    <form onSubmit={submitAttendance} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-6">
      <h2 className="font-semibold md:col-span-6">{t("hr.manualAttendance")}</h2>
      <p className="text-xs text-muted-foreground md:col-span-6">{t("hr.manualAttendanceHelp")}</p>
      <select required value={attendanceForm.employee_id} onChange={e => setAttendanceForm({ ...attendanceForm, employee_id: e.target.value })} className={fieldClass}>
        <option value="">{t("hr.employee")}</option>{employees.map(employee => <option key={employee.id} value={employee.id}>{employee.employee_no} · {employee.name}</option>)}
      </select>
      <input required type="date" value={attendanceForm.attendance_date} onChange={e => setAttendanceForm({ ...attendanceForm, attendance_date: e.target.value })} className={fieldClass} />
      <label className="text-xs">حضور<input required type="datetime-local" value={attendanceForm.check_in_time} onChange={e => setAttendanceForm({ ...attendanceForm, check_in_time: e.target.value })} className={fieldClass} /></label>
      <label className="text-xs">انصراف<input type="datetime-local" value={attendanceForm.check_out_time} onChange={e => setAttendanceForm({ ...attendanceForm, check_out_time: e.target.value })} className={fieldClass} /></label>
      <button disabled={busy || !companyId || !employees.length} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{t("hr.record")}</button>
    </form>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">{t("hr.attendanceLog")}</h2>
      {attendance.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noAttendance")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.employee")}</th><th className="p-2 text-right">التاريخ</th><th className="p-2 text-right">الحضور</th><th className="p-2 text-right">الانصراف</th><th className="p-2 text-right">المصدر</th><th className="p-2 text-right">إجراء</th></tr></thead><tbody>{attendance.map(record => <tr key={record.id} className="border-b"><td className="p-2">{employeeName(record.employee_id)}</td><td className="p-2">{formatCompanyDate(record.attendance_date, dateFormat)}</td><td className="p-2">{displayDateTime(record.check_in_at)}</td><td className="p-2">{displayDateTime(record.check_out_at)}</td><td className="p-2">{t(`hr.attendanceSources.${record.source}`, { defaultValue: record.source })}</td><td className="p-2"><button type="button" onClick={() => editCorrection(record)} className="rounded border px-2 py-1">{t("hr.requestCorrection")}</button></td></tr>)}</tbody></table></div>}
      {correctionTarget !== null && <form onSubmit={submitCorrection} className="grid gap-3 rounded-xl border p-4 md:grid-cols-4">
        <h3 className="font-medium md:col-span-4">{t("hr.correctRecord")} #{correctionTarget}</h3>
        <label className="text-xs">{t("hr.checkIn")}<input required type="datetime-local" value={correctionForm.check_in_time} onChange={e => setCorrectionForm({ ...correctionForm, check_in_time: e.target.value })} className={fieldClass} /></label>
        <label className="text-xs">{t("hr.checkOut")}<input type="datetime-local" value={correctionForm.check_out_time} onChange={e => setCorrectionForm({ ...correctionForm, check_out_time: e.target.value })} className={fieldClass} /></label>
        <input required value={correctionForm.reason} onChange={e => setCorrectionForm({ ...correctionForm, reason: e.target.value })} placeholder="{t("hr.correctionReason")}" className={fieldClass} />
        <div className="flex gap-2"><button disabled={busy} className="rounded bg-primary px-3 py-2 text-primary-foreground">{t("hr.send")}</button><button type="button" onClick={() => setCorrectionTarget(null)} className="rounded border px-3 py-2">{t("hr.cancel")}</button></div>
      </form>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">{t("hr.correctionRequests")}</h2>
      {corrections.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noCorrectionRequests")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.record")}</th><th className="p-2 text-right">{t("hr.proposedCheckIn")}</th><th className="p-2 text-right">{t("hr.proposedCheckOut")}</th><th className="p-2 text-right">{t("hr.reason")}</th><th className="p-2 text-right">{t("hr.status")}</th><th className="p-2 text-right">{t("hr.decision")}</th></tr></thead><tbody>{corrections.map(item => <tr key={item.id} className="border-b"><td className="p-2">#{item.attendance_record_id}</td><td className="p-2">{displayDateTime(item.proposed_check_in_at)}</td><td className="p-2">{displayDateTime(item.proposed_check_out_at)}</td><td className="p-2">{item.reason}</td><td className="p-2">{t(`hr.statuses.${item.status}`, { defaultValue: item.status })}</td><td className="p-2">{item.status === "pending" ? <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => void decideCorrection(item.id, "approve")} className="rounded border px-2 py-1">{t("hr.approve")}</button><button type="button" disabled={busy} onClick={() => void decideCorrection(item.id, "reject")} className="rounded border px-2 py-1 text-destructive">{t("hr.reject")}</button></div> : "—"}</td></tr>)}</tbody></table></div>}
    </section>

    <form onSubmit={submitOvertime} className="grid gap-3 rounded-2xl border bg-card p-5 md:grid-cols-4">
      <h2 className="font-semibold md:col-span-4">{t("hr.overtimeRequest")}</h2>
      <p className="text-xs text-muted-foreground md:col-span-4">الحد {t("hr.available")} يُحسب {t("hr.from")} {t("hr.checkIn")} والانصراف مطروحًا {t("hr.from")}ه ساعات العمل اليومية في إعدادات الشركة. الطلبات ال{t("hr.from")}تظرة تُحجز حتى لا تتجاوز الطلبات إجمالي {t("hr.hours")} المسجلة.</p>
      <select required value={overtimeForm.attendance_record_id} onChange={e => setOvertimeForm({ ...overtimeForm, attendance_record_id: e.target.value })} className={fieldClass}>
        <option value="">{t("hr.attendanceLog")}</option>{attendance.filter(record => record.check_out_at).map(record => <option key={record.id} value={record.id}>{employeeName(record.employee_id)} · {formatCompanyDate(record.attendance_date, dateFormat)}</option>)}
      </select>
      <input required type="number" min="0.01" step="0.01" value={overtimeForm.requested_hours} onChange={e => setOvertimeForm({ ...overtimeForm, requested_hours: e.target.value })} placeholder="{t("hr.hours")}" className={fieldClass} />
      <input required value={overtimeForm.reason} onChange={e => setOvertimeForm({ ...overtimeForm, reason: e.target.value })} placeholder="{t("hr.overtimeReason")}" className={fieldClass} />
      <button disabled={busy || !companyId || !attendance.some(record => record.check_out_at)} className="rounded-lg bg-primary px-4 py-2 text-primary-foreground disabled:opacity-50">{t("hr.submitRequest")}</button>
    </form>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">طلبات {t("hr.hours")} الإضافية</h2>
      {overtimeRequests.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noRequests")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.employee")}</th><th className="p-2 text-right">التاريخ</th><th className="p-2 text-right">{t("hr.hours")}</th><th className="p-2 text-right">{t("hr.reason")}</th><th className="p-2 text-right">{t("hr.status")}</th><th className="p-2 text-right">ال{t("hr.decision")}</th></tr></thead><tbody>{overtimeRequests.map(request => { const record = attendance.find(item => item.id === request.attendance_record_id); return <tr key={request.id} className="border-b"><td className="p-2">{record ? employeeName(record.employee_id) : "—"}</td><td className="p-2">{record ? formatCompanyDate(record.attendance_date, dateFormat) : "—"}</td><td className="p-2">{request.requested_hours}</td><td className="p-2">{request.reason}</td><td className="p-2">{t(`hr.statuses.${request.status}`, { defaultValue: request.status })}</td><td className="p-2">{request.status === "pending" ? <div className="flex gap-2"><button type="button" disabled={busy} onClick={() => void decideOvertime(request.id, "approve")} className="rounded border px-2 py-1">{t("hr.approve")}</button><button type="button" disabled={busy} onClick={() => void decideOvertime(request.id, "reject")} className="rounded border px-2 py-1 text-destructive">{t("hr.reject")}</button></div> : "—"}</td></tr>; })}</tbody></table></div>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">{t("hr.leaveBalances")}</h2>
      {balances.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noLeaveBalances")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.employee")}</th><th className="p-2 text-right">{t("hr.type")}</th><th className="p-2 text-right">{t("hr.entitled")}</th><th className="p-2 text-right">{t("hr.consumed")}</th><th className="p-2 text-right">{t("hr.available")}</th></tr></thead><tbody>{balances.map(balance => <tr key={balance.id} className="border-b"><td className="p-2">{employeeName(balance.employee_id)}</td><td className="p-2">{leaveTypeLabel[balance.leave_type] || balance.leave_type}</td><td className="p-2">{balance.entitled_days}</td><td className="p-2">{balance.consumed_days}</td><td className="p-2">{balance.available_days}</td></tr>)}</tbody></table></div>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <div className="flex items-center justify-between"><h2 className="font-semibold">{t("hr.leaveRequests")}</h2><button type="button" onClick={() => void load()} className="rounded-lg border px-3 py-1.5 text-sm">{t("hr.refresh")}</button></div>
      {requests.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noRequests")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.employee")}</th><th className="p-2 text-right">{t("hr.type")}</th><th className="p-2 text-right">{t("hr.period")}</th><th className="p-2 text-right">{t("hr.days")}</th><th className="p-2 text-right">{t("hr.status")}</th><th className="p-2 text-right">{t("hr.reason")}</th><th className="p-2 text-right">{t("hr.action")}</th></tr></thead><tbody>{requests.map(request => <tr key={request.id} className="border-b"><td className="p-2">{employeeName(request.employee_id)}</td><td className="p-2">{leaveTypeLabel[request.leave_type] || request.leave_type}</td><td className="p-2">{formatCompanyDate(request.start_date, dateFormat)} → {formatCompanyDate(request.end_date, dateFormat)}</td><td className="p-2">{request.requested_days}</td><td className="p-2">{request.status}</td><td className="max-w-48 truncate p-2" title={request.reason || ""}>{request.reason || "—"}</td><td className="p-2">{request.status === "pending" ? <div className="flex gap-2"><button disabled={busy} onClick={() => void decide(request.id, "approve")} className="rounded border px-2 py-1">{t("hr.approve")}</button><button disabled={busy} onClick={() => void decide(request.id, "reject")} className="rounded border px-2 py-1 text-destructive">{t("hr.reject")}</button></div> : request.decision_reason || "—"}</td></tr>)}</tbody></table></div>}
    </section>

    <section className="space-y-3 rounded-2xl border bg-card p-5">
      <h2 className="font-semibold">{t("hr.companyUserProfiles")}</h2>
      {workforce.length === 0 ? <p className="text-sm text-muted-foreground">{t("hr.noCompanyUsers")}</p> : <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b"><th className="p-2 text-right">{t("hr.consumed")}</th><th className="p-2 text-right">الاسم</th><th className="p-2 text-right">{t("hr.phone")}</th><th className="p-2 text-right">{t("hr.address")}</th><th className="p-2 text-right">إجراء</th></tr></thead><tbody>{workforce.map((user:any) => <tr key={user.id} className="border-b"><td className="p-2">{user.username}</td><td className="p-2"><input value={user.full_name || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, full_name: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><input value={user.phone || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, phone: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><input value={user.address || ""} onChange={e => setWorkforce(workforce.map(row => row.id === user.id ? { ...row, address: e.target.value } : row))} className="rounded border px-2 py-1" /></td><td className="p-2"><button disabled={busy} onClick={() => void saveWorkforce(user)} className="rounded border px-3 py-1">{t("hr.save")}</button></td></tr>)}</tbody></table></div>}
    </section>
  </section>;
}
