import { useEffect, useState } from "react";
import { Boxes, CheckCircle2, PlugZap, Truck, WalletCards } from "lucide-react";

type Template = { code: string; name: string; country_code: string; payment_methods: string[]; cod: boolean; settlement: string; services: string[] };
type Provider = { id: number; code: string; name: string; country_code: string; api_enabled: boolean; active: boolean };
type Connection = { id: number; provider_code: string; provider_name: string; name: string; environment: string; auth_type: string; enabled: boolean; manifest?: { capabilities: string[] } };

async function getJson<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: "include" });
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

export default function ShippingPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [connections, setConnections] = useState<Connection[]>([]);
  const [error, setError] = useState("");

  const load = async () => {
    setError("");
    try {
      const [t, p, c] = await Promise.all([
        getJson<{ data: Template[] }>("/api/v1/shipping/provider-templates"),
        getJson<Provider[]>("/api/v1/shipping/providers"),
        getJson<Connection[]>("/api/v1/shipping/connections"),
      ]);
      setTemplates(t.data ?? []); setProviders(p); setConnections(c);
    } catch (e) { setError(e instanceof Error ? e.message : "تعذر تحميل بيانات الشحن"); }
  };

  useEffect(() => { void load(); }, []);

  return (
    <div className="mx-auto w-full max-w-[1600px] space-y-6" dir="rtl">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div><h1 className="text-3xl font-bold tracking-tight">الشحن واللوجستيات</h1><p className="mt-1 text-sm text-muted-foreground">شركات الشحن، الدفع، COD، التتبع، التسويات والتكاملات.</p></div>
        <button onClick={() => void load()} className="rounded-xl border bg-card px-4 py-2 text-sm font-medium">تحديث</button>
      </header>
      {error && <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm">{error}</div>}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[{icon:Truck,title:"شركات الشحن",value:providers.length},{icon:WalletCards,title:"الدفع والتحصيل",value:"COD / Invoice / Prepaid"},{icon:Boxes,title:"التسويات",value:"COD Reconciliation"},{icon:PlugZap,title:"التكاملات",value:connections.length}].map(({icon:Icon,title,value}) => (
          <div key={title} className="rounded-2xl border bg-card p-5 shadow-sm"><Icon className="mb-3 h-5 w-5"/><div className="text-sm text-muted-foreground">{title}</div><div className="mt-1 text-xl font-semibold">{value}</div></div>
        ))}
      </section>

      <section className="rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="text-xl font-semibold">الاتصالات المفعلة</h2>
        <p className="mt-1 text-xs text-muted-foreground">المفاتيح وكلمات المرور لا تُحفظ داخل قاعدة البيانات؛ يتم استخدام Secret Reference وقت التشغيل.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {connections.map(c => <article key={c.id} className="rounded-xl border p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{c.provider_name}</h3><CheckCircle2 className="h-4 w-4"/></div><div className="mt-1 text-xs text-muted-foreground">{c.name} · {c.environment} · {c.auth_type}</div><div className="mt-3 text-xs">{c.manifest?.capabilities?.join(" · ")}</div></article>)}
          {!connections.length && <div className="text-sm text-muted-foreground">لا توجد Connections مضافة حتى الآن.</div>}
        </div>
      </section>

      <section className="rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="text-xl font-semibold">قوالب شركات الشحن</h2><p className="mt-1 text-xs text-muted-foreground">القوالب نقطة بداية فقط؛ الأسعار وشروط COD والتسوية تعتمد على عقد العميل الحالي.</p>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {templates.map(t => <article key={t.code} className="rounded-xl border p-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{t.name}</h3><span className="rounded-full bg-muted px-2 py-1 text-xs">{t.country_code}</span></div><div className="mt-3 text-sm">COD: {t.cod ? "متاح" : "غير افتراضي"}</div><div className="mt-1 text-sm text-muted-foreground">الدفع: {t.payment_methods.join(" · ")}</div><div className="mt-1 text-sm text-muted-foreground">الخدمات: {t.services.join(" · ")}</div><div className="mt-1 text-sm text-muted-foreground">التسوية: {t.settlement}</div></article>)}
        </div>
      </section>
    </div>
  );
}
