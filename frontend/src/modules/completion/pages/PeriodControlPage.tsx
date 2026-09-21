import { useState } from "react";
import { api } from "../../../lib/api";

export default function PeriodControlPage() {
  const [companyId, setCompanyId] = useState("");
  const [periodKey, setPeriodKey] = useState("");
  const [message, setMessage] = useState("");
  const lock = async () => {
    setMessage("");
    try {
      await api(`/completion/periods/${Number(companyId)}/${encodeURIComponent(periodKey)}/lock`, { method: "POST" });
      setMessage("Period locked successfully.");
    } catch (error) { setMessage(error instanceof Error ? error.message : "Unable to lock period."); }
  };
  return <section><h1>Period Control</h1><label>Company <input value={companyId} onChange={e=>setCompanyId(e.target.value)} /></label><label>Period <input value={periodKey} onChange={e=>setPeriodKey(e.target.value)} placeholder="2026-09" /></label><button disabled={!companyId || !periodKey} onClick={lock}>Lock period</button>{message && <p>{message}</p>}</section>;
}