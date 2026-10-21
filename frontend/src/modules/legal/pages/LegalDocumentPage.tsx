import { useEffect, useState } from "react";
import { ArrowRight, FileText, Loader2, ShieldCheck } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { getLegalDocument, type LegalDocumentType } from "@/modules/legal/services/legal.service";

export default function LegalDocumentPage() {
  const location = useLocation();
  const documentType: LegalDocumentType = location.pathname === "/privacy" ? "privacy" : "terms";
  const [document,setDocument]=useState<Awaited<ReturnType<typeof getLegalDocument>>|null>(null);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{let active=true;setLoading(true);getLegalDocument(documentType).then(data=>{if(active)setDocument(data)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[documentType]);
  const privacy=documentType==="privacy";
  const title=document ? document.title_ar : (privacy ? "سياسة الخصوصية" : "شروط الاستخدام");
  const content=document?.content_ar??"";
  return <main className="min-h-screen bg-slate-950 px-4 py-8 sm:px-6 sm:py-12" dir="rtl"><div className="mx-auto max-w-5xl">
    <div className="mb-6 flex items-center justify-between gap-4"><Link to="/login" className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-bold text-slate-200 hover:bg-white/10"><ArrowRight className="size-4"/>العودة لتسجيل الدخول</Link><div className="flex items-center gap-2 text-sm font-black text-white"><span className="flex size-9 items-center justify-center rounded-xl bg-blue-600">P</span>PrimeERP</div></div>
    <article className="overflow-hidden rounded-[30px] border border-white/10 bg-white shadow-2xl"><header className="bg-[radial-gradient(circle_at_top_right,rgba(59,130,246,.35),transparent_35%),#0f172a] px-6 py-9 text-white sm:px-10"><div className="flex items-center gap-3 text-blue-300">{privacy?<ShieldCheck className="size-6"/>:<FileText className="size-6"/>}<span className="text-sm font-bold">PrimeERP • المستند القانوني</span></div><h1 className="mt-4 text-3xl font-black sm:text-4xl">{title}</h1>{document&&<p className="mt-3 text-sm text-slate-400">الإصدار {document.version}{document.published_at ? " • منشور" : ""}</p>}</header>
    <section className="px-6 py-9 sm:px-10 sm:py-12">{loading?<div className="flex min-h-72 items-center justify-center text-slate-500"><Loader2 className="ml-2 size-5 animate-spin"/>جاري تحميل المستند...</div>:<div className="whitespace-pre-wrap text-[15px] leading-8 text-slate-700">{content}</div>}</section></article>
    <p className="mt-5 text-center text-xs text-slate-500">يمكن لمالك المنصة تحديث هذا المستند من لوحة Super Admin.</p>
  </div></main>;
}
