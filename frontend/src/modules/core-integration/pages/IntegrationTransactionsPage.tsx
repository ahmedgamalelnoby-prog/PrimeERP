import { useEffect, useState } from "react";
import { api } from "../../../lib/api";

type Tx = { id:number; status:string; company_id:number; transaction_type?:string; created_at?:string };
export default function IntegrationTransactionsPage() {
 const [rows,setRows]=useState<Tx[]>([]); const [companyId,setCompanyId]=useState(""); const [error,setError]=useState("");
 useEffect(()=>{ if(!companyId)return; api<Tx[]>(`/core/integration/transactions?company_id=${Number(companyId)}`).then(setRows).catch(e=>setError(e instanceof Error?e.message:"Request failed")); },[companyId]);
 return <section><h1>Core Integration Transactions</h1><input value={companyId} onChange={e=>setCompanyId(e.target.value)} placeholder="Company ID"/>{error&&<p>{error}</p>}<table><thead><tr><th>ID</th><th>Type</th><th>Status</th></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td>{r.id}</td><td>{r.transaction_type||"—"}</td><td>{r.status}</td></tr>)}</tbody></table></section>;
}