import {useEffect,useState} from "react";
import client from "@/shared/api/client";
const company=()=>Number(localStorage.getItem("company_id")||0);
type Device={id:number;device_uid:string;name:string;platform:string};
type Task={id:number;title:string;task_type:string;status:string};
export default function MobilePage(){
 const [devices,setDevices]=useState<Device[]>([]),[tasks,setTasks]=useState<Task[]>([]),[uid,setUid]=useState(localStorage.getItem("mobile_device_uid")||""),[busy,setBusy]=useState(false),[msg,setMsg]=useState("");
 const load=async()=>{if(!company())return;const [d,t]=await Promise.all([client.get<Device[]>("/mobile/devices",{params:{company_id:company()}}),client.get<Task[]>("/mobile/tasks",{params:{company_id:company()}})]);setDevices(d.data);setTasks(t.data)};
 useEffect(()=>{load().catch(e=>setMsg(e?.message||"تعذر التحميل"))},[]);
 const register=async()=>{if(!uid)return;setBusy(true);try{await client.post("/mobile/devices",{company_id:company(),device_uid:uid,name:"PrimeERP Mobile",platform:"web-pwa",app_version:"1.0"});localStorage.setItem("mobile_device_uid",uid);await load();setMsg("تم تسجيل الجهاز")}catch(e:any){setMsg(e?.response?.data?.detail||"فشل التسجيل")}finally{setBusy(false)}};
 const complete=async(id:number)=>{await client.post("/mobile/tasks/"+id+"/complete");await load()};
 return <section className="space-y-6 p-6" dir="rtl"><header><h1 className="text-2xl font-bold">PrimeERP Mobile</h1><p className="text-sm text-muted-foreground">تشغيل ميداني، أجهزة، مهام، ومسار عمل قابل للعمل مع انقطاع الشبكة.</p></header>
 <div className="grid gap-4 md:grid-cols-3"><div className="rounded-2xl border p-5"><h2 className="font-semibold">ربط الجهاز</h2><input className="mt-3 w-full rounded border p-2" value={uid} onChange={e=>setUid(e.target.value)} placeholder="Device UID"/><button disabled={busy||!company()} onClick={register} className="mt-3 rounded bg-primary px-4 py-2 text-primary-foreground">تسجيل</button></div>
 <div className="rounded-2xl border p-5"><h2 className="font-semibold">الأجهزة</h2><p className="mt-2 text-3xl font-bold">{devices.length}</p><p className="text-sm text-muted-foreground">أجهزة مرتبطة بهذا المستخدم</p></div>
 <div className="rounded-2xl border p-5"><h2 className="font-semibold">المهام المفتوحة</h2><p className="mt-2 text-3xl font-bold">{tasks.filter(x=>x.status!=="completed").length}</p></div></div>
 <div className="rounded-2xl border p-5"><h2 className="mb-4 font-semibold">مهام التنفيذ</h2>{tasks.length?<div className="space-y-2">{tasks.map(t=><div key={t.id} className="flex items-center justify-between rounded-lg border p-3"><span>{t.title} <small className="mr-2 text-muted-foreground">{t.task_type}</small></span>{t.status!=="completed"&&<button onClick={()=>complete(t.id)} className="rounded border px-3 py-1">إنهاء</button>}</div>)}</div>:<p className="text-sm text-muted-foreground">لا توجد مهام حالياً.</p>}</div>
 {msg&&<p className="text-sm">{msg}</p>}</section>
}