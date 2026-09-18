import { useEffect, useState } from "react";
import client from "@/shared/api/client";

type Permission = { id:number; name:string; resource:string; action:string; description:string|null; is_active:boolean; };

export default function PermissionsPage() {
  const [rows,setRows]=useState<Permission[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");
  const [busy,setBusy]=useState<number|null>(null);
  const load=async()=>{setLoading(true);setError("");try{const r=await client.get<Permission[]>("/roles/permissions");setRows(r.data)}catch(e:any){setError(e?.response?.data?.detail||"تعذر تحميل الصلاحيات")}finally{setLoading(false)}};
  useEffect(()=>{void load()},[]);
  const toggle=async(p:Permission)=>{setBusy(p.id);setError("");try{await client.put(`/roles/permissions/${p.id}`,{is_active:!p.is_active});await load()}catch(e:any){setError(e?.response?.data?.detail||"تعذر تحديث الصلاحية")}finally{setBusy(null)}};
  return <section className="space-y-6 p-6" dir="rtl"><header><h1 className="text-2xl font-bold">الصلاحيات</h1><p className="mt-1 text-sm text-muted-foreground">عرض وإدارة صلاحيات النظام وربطها بالأدوار.</p></header>{error&&<div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">{error}</div>}<div className="overflow-hidden rounded-2xl border bg-card shadow-sm"><div className="flex items-center justify-between border-b p-4"><h2 className="font-semibold">دليل الصلاحيات</h2><button className="rounded-lg border px-3 py-1.5 text-sm" onClick={()=>void load()}>تحديث</button></div>{loading?<div className="p-8 text-center">جاري التحميل...</div>:<div className="overflow-auto"><table className="w-full min-w-[760px] text-sm"><thead><tr className="border-b bg-muted/40 text-right"><th className="p-3">الاسم</th><th className="p-3">المورد</th><th className="p-3">الإجراء</th><th className="p-3">الوصف</th><th className="p-3">الحالة</th><th className="p-3">إجراء</th></tr></thead><tbody>{rows.map(p=><tr key={p.id} className="border-b last:border-0"><td className="p-3 font-medium">{p.name}</td><td className="p-3">{p.resource}</td><td className="p-3">{p.action}</td><td className="p-3">{p.description||"—"}</td><td className="p-3">{p.is_active?"نشطة":"متوقفة"}</td><td className="p-3"><button disabled={busy===p.id} onClick={()=>void toggle(p)} className="rounded-lg border px-3 py-1.5 text-xs">{busy===p.id?"...":p.is_active?"تعطيل":"تفعيل"}</button></td></tr>)}</tbody></table>{!rows.length&&<div className="p-8 text-center text-muted-foreground">لا توجد صلاحيات.</div>}</div>}</div></section>;
}