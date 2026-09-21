import { useMemo, useState } from "react";
import { toast } from "react-hot-toast";
import { posApi } from "../services/pos.service";
import type { PaymentMethod, POSOrder, POSSession } from "../types/pos";

const input = "w-full rounded-xl border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/30";
const card = "rounded-2xl border bg-card p-5 shadow-sm";

export default function PosPage() {
  const [companyId,setCompanyId]=useState("");
  const [branchId,setBranchId]=useState("");
  const [locationId,setLocationId]=useState("");
  const [outletId,setOutletId]=useState("");
  const [deviceId,setDeviceId]=useState("");
  const [cashierId,setCashierId]=useState("");
  const [session,setSession]=useState<POSSession|null>(null);
  const [order,setOrder]=useState<POSOrder|null>(null);
  const [number,setNumber]=useState("");
  const [itemId,setItemId]=useState("");
  const [variantId,setVariantId]=useState("");
  const [qty,setQty]=useState("1");
  const [price,setPrice]=useState("");
  const [tax,setTax]=useState("0");
  const [method,setMethod]=useState<PaymentMethod>("cash");
  const [amount,setAmount]=useState("");
  const [paymentKey,setPaymentKey]=useState("");
  const [closing,setClosing]=useState("");
  const [busy,setBusy]=useState(false);

  const cid=Number(companyId);
  const total=order?.total ?? 0;
  const outstanding=Math.max(0,total-(order?.paid_total ?? 0));

  async function act(fn:()=>Promise<void>) {
    setBusy(true);
    try { await fn(); } catch(error:any) { toast.error(error?.response?.data?.detail ?? error?.message ?? "تعذر تنفيذ العملية."); } finally { setBusy(false); }
  }

  const openReady=useMemo(()=>cid>0 && Number(outletId)>0 && Number(deviceId)>0 && Number(cashierId)>0,[cid,outletId,deviceId,cashierId]);

  return <section className="mx-auto w-full max-w-[1400px] space-y-6" dir="rtl">
    <header>
      <p className="text-sm font-semibold text-primary">نقطة البيع</p>
      <h1 className="mt-1 text-3xl font-bold">تشغيل POS</h1>
      <p className="mt-2 text-sm text-muted-foreground">مسار تشغيلي مترابط: Outlet → Device → Cashier → Session → Order → Payment → EOD.</p>
    </header>

    <div className="grid gap-6 xl:grid-cols-2">
      <section className={card}>
        <h2 className="text-lg font-semibold">1. فتح الجلسة</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {[["الشركة",companyId,setCompanyId],["الفرع",branchId,setBranchId],["المخزن/الموقع",locationId,setLocationId],["Outlet",outletId,setOutletId],["Device",deviceId,setDeviceId],["الكاشير",cashierId,setCashierId]].map(([label,value,setValue])=><label key={String(label)} className="space-y-1 text-sm"><span>{label}</span><input className={input} value={String(value)} onChange={e=>(setValue as (v:string)=>void)(e.target.value)} inputMode="numeric"/></label>)}
        </div>
        <button disabled={busy||!openReady} className="mt-4 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" onClick={()=>void act(async()=>{const s=await posApi.openSession({company_id:cid,outlet_id:Number(outletId),device_id:Number(deviceId),cashier_user_id:Number(cashierId)});setSession(s);toast.success("تم فتح جلسة POS.");})}>فتح الجلسة</button>
        {session && <p className="mt-3 rounded-xl bg-muted p-3 text-sm">الجلسة #{session.id} — الحالة: <b>{session.status}</b></p>}
      </section>

      <section className={card}>
        <h2 className="text-lg font-semibold">2. إنشاء الطلب</h2>
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label className="space-y-1 text-sm"><span>رقم الطلب</span><input className={input} value={number} onChange={e=>setNumber(e.target.value)}/></label>
          <label className="space-y-1 text-sm"><span>Item ID</span><input className={input} value={itemId} onChange={e=>setItemId(e.target.value)} inputMode="numeric"/></label>
          <label className="space-y-1 text-sm"><span>Variant ID (اختياري)</span><input className={input} value={variantId} onChange={e=>setVariantId(e.target.value)} inputMode="numeric"/></label>
          <label className="space-y-1 text-sm"><span>الكمية</span><input className={input} value={qty} onChange={e=>setQty(e.target.value)} inputMode="decimal"/></label>
          <label className="space-y-1 text-sm"><span>سعر الوحدة</span><input className={input} value={price} onChange={e=>setPrice(e.target.value)} inputMode="decimal"/></label>
          <label className="space-y-1 text-sm"><span>الضريبة %</span><input className={input} value={tax} onChange={e=>setTax(e.target.value)} inputMode="decimal"/></label>
        </div>
        <button disabled={busy||!session||!number||!itemId||!price} className="mt-4 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" onClick={()=>void act(async()=>{const o=await posApi.createOrder({company_id:cid,session_id:session!.id,number,lines:[{item_id:Number(itemId),variant_id:variantId?Number(variantId):null,quantity:Number(qty),unit_price:Number(price),tax_percent:Number(tax)}]});setOrder(o);toast.success("تم إنشاء الطلب.");})}>إنشاء الطلب</button>
      </section>
    </div>

    <section className={card}>
      <h2 className="text-lg font-semibold">3. إنهاء الطلب والتحصيل</h2>
      {order ? <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_auto]"><div className="rounded-xl bg-muted p-4 text-sm"><div className="flex justify-between"><span>الطلب</span><b>{order.number}</b></div><div className="mt-2 flex justify-between"><span>الإجمالي</span><b>{order.total.toLocaleString("en-US",{minimumFractionDigits:2})}</b></div><div className="mt-2 flex justify-between"><span>المتبقي</span><b>{outstanding.toLocaleString("en-US",{minimumFractionDigits:2})}</b></div><div className="mt-2 flex justify-between"><span>الحالة</span><b>{order.status}</b></div></div><div className="flex flex-wrap items-end gap-2"><button disabled={busy||order.status!=="draft"} className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" onClick={()=>void act(async()=>{const o=await posApi.finalizeOrder(order.id,cid);setOrder(o);toast.success("تم ترحيل الطلب والمخزون والمحاسبة.");})}>Finalize</button><select className={input+" min-w-28"} value={method} onChange={e=>setMethod(e.target.value as PaymentMethod)}><option value="cash">نقدي</option><option value="card">بطاقة</option><option value="bank">بنك</option><option value="other">أخرى</option></select><input className={input+" w-32"} value={amount} onChange={e=>setAmount(e.target.value)} placeholder="المبلغ"/><input className={input+" w-44"} value={paymentKey} onChange={e=>setPaymentKey(e.target.value)} placeholder="Idempotency key"/><button disabled={busy||order.status!=="finalized"||!amount||!paymentKey} className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50" onClick={()=>void act(async()=>{const p=await posApi.pay({company_id:cid,order_id:order.id,method,amount:Number(amount),idempotency_key:paymentKey});setOrder({...order,paid_total:(order.paid_total??0)+p.amount});toast.success("تم تسجيل التحصيل وترحيله.");})}>تحصيل</button></div></div> : <p className="mt-3 text-sm text-muted-foreground">أنشئ طلبًا أولًا.</p>}
    </section>

    <section className={card}>
      <h2 className="text-lg font-semibold">4. إغلاق الجلسة والمطابقة</h2>
      <div className="mt-4 flex flex-wrap items-end gap-3"><label className="space-y-1 text-sm"><span>إجمالي الإغلاق</span><input className={input+" w-48"} value={closing} onChange={e=>setClosing(e.target.value)} inputMode="decimal"/></label><button disabled={busy||!session||session.status!=="open"||!closing} className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground disabled:opacity-50" onClick={()=>void act(async()=>{const s=await posApi.closeSession(session!.id,{company_id:cid,closing_total:Number(closing)});setSession(s);toast.success("تم إغلاق الجلسة بعد مطابقة التحصيل.");})}>إغلاق الجلسة</button></div>
      <p className="mt-3 text-xs text-muted-foreground">المطابقة النهائية تتم في الـbackend على المدفوعات المرحّلة، وليس على رقم يدخله المستخدم فقط.</p>
    </section>
  </section>;
}
