import { useEffect, useState } from "react";
import { ArrowLeft, Bot, Boxes, CheckCircle2, Clock3, Map, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import client from "@/shared/api/client";
import { Button } from "@/components/ui/button";

type ModuleInfo={key:string;name:string;name_ar:string;group:string;status:string;description:string};

export default function ModuleWorkbenchPage({moduleKey}:{moduleKey:string}){
  const [module,setModule]=useState<ModuleInfo|null>(null);
  const [loading,setLoading]=useState(true);
  useEffect(()=>{let alive=true;client.get("/platform/modules/"+moduleKey).then(r=>{if(alive)setModule(r.data?.module||null);}).catch(()=>setModule(null)).finally(()=>{if(alive)setLoading(false);});return()=>{alive=false;};},[moduleKey]);
  const status=module?.status;
  const statusText=status==="active"?"تشغيلي":status==="foundation"?"أساس وقيد الاستكمال":"خارطة طريق";
  const StatusIcon=status==="active"?CheckCircle2:status==="foundation"?Clock3:Map;
  return <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8" dir="rtl"><div className="mx-auto max-w-5xl">
    <div className="overflow-hidden rounded-3xl bg-slate-950 p-7 text-white shadow-xl sm:p-9">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between"><div><div className="mb-3 inline-flex items-center gap-2 rounded-full bg-cyan-400/10 px-3 py-1.5 text-xs font-bold text-cyan-300"><Boxes className="size-4"/>PrimeERP Module Workbench</div><h1 className="text-3xl font-black">{loading?"جاري تحميل الموديول...":module?.name_ar||"الموديول"}</h1><p className="mt-2 text-sm text-slate-300">{module?.name||moduleKey}</p></div>{module&&<div className="rounded-2xl bg-white/5 px-4 py-3 text-center"><StatusIcon className="mx-auto size-5"/><div className="mt-1 text-xs font-bold">{statusText}</div></div>}</div>
    </div>
    <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_320px]">
      <section className="rounded-3xl border bg-white p-6 shadow-sm"><h2 className="text-lg font-black">نطاق الموديول</h2><p className="mt-3 text-sm leading-7 text-slate-600">{module?.description||"لم يتم العثور على تعريف هذا الموديول في الـModule Registry."}</p><div className="mt-6 grid gap-3 sm:grid-cols-2"><div className="rounded-2xl bg-slate-50 p-4"><div className="text-xs text-slate-400">Module Key</div><div className="mt-1 font-mono text-sm font-bold">{moduleKey}</div></div><div className="rounded-2xl bg-slate-50 p-4"><div className="text-xs text-slate-400">Group</div><div className="mt-1 text-sm font-bold">{module?.group||"-"}</div></div></div>
      <div className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/60 p-4"><div className="flex items-center gap-2 font-bold text-blue-950"><Sparkles className="size-4"/><span>Prime AI</span></div><p className="mt-2 text-xs leading-6 text-blue-900/70">استخدم مساعد Prime AI لشرح خطوات العمل الحالية، اقتراح طريقة تشغيل الموديول، وتحديد الوظائف المطلوبة قبل أي تطوير جديد.</p><Link to="/helpdesk"><Button className="mt-3 rounded-xl"><Bot className="me-2 size-4"/>فتح AI Help Desk</Button></Link></div>
      </section>
      <aside className="rounded-3xl border bg-white p-6 shadow-sm"><h2 className="font-black">تحديثات الموديول</h2><ul className="mt-4 space-y-3 text-sm text-slate-600"><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600"/>التعريف مركزي في Module Registry</li><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600"/>الـAI يستخدم نفس المعرفة المركزية</li><li className="flex gap-2"><CheckCircle2 className="mt-0.5 size-4 shrink-0 text-emerald-600"/>أي تغيير كبير يجب أن يمر بالـRelease Gate</li></ul><Link to="/modules" className="mt-6 inline-flex items-center text-sm font-bold text-blue-600 hover:underline"><ArrowLeft className="me-2 size-4"/>العودة للكتالوج</Link></aside>
    </div>
  </div></div>;
}
