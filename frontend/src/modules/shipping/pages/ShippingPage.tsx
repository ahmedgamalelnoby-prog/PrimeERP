import { useEffect, useState } from "react";
import { Boxes, CheckCircle2, Truck, WalletCards } from "lucide-react";

type Template = { code: string; name: string; country_code: string; payment_methods: string[]; cod: boolean; settlement: string; services: string[] };
type Provider = { id: number; code: string; name: string; country_code: string; api_enabled: boolean; active: boolean };

export default function ShippingPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [tenantId, setTenantId] = useState("1");

  useEffect(() => {
    fetch("/api/v1/shipping/provider-templates").then(r => r.json()).then(r => setTemplates(r.data ?? [])).catch(() => setTemplates([]));
  }, []);

  const loadProviders = () => {
    fetch(`/api/v1/shipping/providers?tenant_id=${tenantId}`).then(r => r.json()).then(setProviders).catch(() => setProviders([]));
  };

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6" dir="rtl">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">الشحن واللوجستيات</h1>
        <p className="mt-1 text-sm text-muted-foreground">شركات الشحن، COD، التسويات، التتبع، والتكاملات في مكان واحد.</p>
      </header>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[{icon:Truck,title:"شركات الشحن",value:providers.length},{icon:WalletCards,title:"ملفات الدفع",value:"COD / Invoice / Prepaid"},{icon:Boxes,title:"التسويات",value:"COD Reconciliation"},{icon:CheckCircle2,title:"التتبع",value:"Tracking & Webhooks"}].map(({icon:Icon,title,value}) => (
          <div key={title} className="rounded-2xl border bg-card p-5 shadow-sm"><Icon className="mb-3 h-5 w-5"/><div className="text-sm text-muted-foreground">{title}</div><div className="mt-1 text-xl font-semibold">{value}</div></div>
        ))}
      </section>

      <section className="rounded-2xl border bg-card p-5 shadow-sm">
        <div className="flex flex-wrap items-end gap-3">
          <label className="grid gap-1 text-sm"><span>Tenant ID</span><input value={tenantId} onChange={e => setTenantId(e.target.value)} className="h-10 w-40 rounded-lg border bg-background px-3" /></label>
          <button onClick={loadProviders} className="h-10 rounded-lg bg-primary px-4 text-sm font-medium text-primary-foreground">تحميل الشركات</button>
        </div>
        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {providers.map(p => <div key={p.id} className="rounded-xl border p-4"><div className="font-semibold">{p.name}</div><div className="mt-1 text-xs text-muted-foreground">{p.code} · {p.country_code}</div><div className="mt-3 text-xs">{p.api_enabled ? "API مفعّل" : "إعداد يدوي"}</div></div>)}
          {!providers.length && <div className="text-sm text-muted-foreground">لا توجد شركات مضافة لهذا الـTenant بعد.</div>}
        </div>
      </section>

      <section className="rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="text-xl font-semibold">قوالب شركات الشحن</h2>
        <p className="mt-1 text-xs text-muted-foreground">القوالب نقطة بداية فقط؛ الرسوم وشروط COD والتسوية يجب اعتمادها من عقد العميل الحالي.</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {templates.map(t => <article key={t.code} className="rounded-xl border p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{t.name}</h3><span className="rounded-full bg-muted px-2 py-1 text-xs">{t.country_code}</span></div><div className="mt-3 text-sm">COD: {t.cod ? "متاح" : "غير افتراضي"}</div><div className="mt-1 text-sm text-muted-foreground">الدفع: {t.payment_methods.join(" · ")}</div><div className="mt-1 text-sm text-muted-foreground">الخدمات: {t.services.join(" · ")}</div><div className="mt-1 text-sm text-muted-foreground">التسوية: {t.settlement}</div></article>)}
        </div>
      </section>
    </div>
  );
}
