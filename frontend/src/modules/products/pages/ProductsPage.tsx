import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { productsApi, type Category, type PriceList, type Recipe, type PricingImpact } from "../api/products.api";

const companyId = () => {
  const value = Number(localStorage.getItem("company_id"));
  return Number.isInteger(value) && value > 0 ? value : null;
};

export default function ProductsPage() {
  const { t, i18n } = useTranslation();
  const [categories,setCategories]=useState<Category[]>([]);
  const [priceLists,setPriceLists]=useState<PriceList[]>([]);
  const [recipes,setRecipes]=useState<Recipe[]>([]);
  const [impact,setImpact]=useState<PricingImpact|null>(null);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState("");

  async function load() {
    const id=companyId();
    if(!id){setError(t("productsHome.activeCompanyRequired"));setLoading(false);return;}
    setLoading(true);setError("");
    try {
      const [c,p,r,i]=await Promise.all([
        productsApi.categories(id),productsApi.priceLists(id),productsApi.recipes(id),productsApi.pricingImpact(id),
      ]);
      setCategories(c);setPriceLists(p);setRecipes(r);setImpact(i);
    } catch(e:any) {
      setError(e?.response?.data?.detail || t("productsHome.loadFailed"));
    } finally { setLoading(false); }
  }

  useEffect(()=>{void load();},[]);

  return <section className="space-y-6 p-6" dir={i18n.dir()}>
    <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
      <div><h1 className="text-2xl font-bold">{t("productsHome.title")}</h1>
      <p className="mt-1 text-sm text-muted-foreground">{t("productsHome.description")}</p></div>
      <button onClick={()=>void load()} className="rounded-lg border px-4 py-2 text-sm">{t("common.refresh")}</button>
    </header>
    {error&&<div className="rounded-xl border bg-destructive/10 p-3 text-sm">{error}</div>}
    {loading?<div className="rounded-2xl border bg-card p-10 text-center">{t("productsHome.loading")}</div>:
    <><div className="grid gap-4 md:grid-cols-4">
      {[[t("productsHome.categories"),categories.length],[t("productsHome.priceLists"),priceLists.length],[t("productsHome.recipes"),recipes.length],[t("productsHome.belowMargin"),impact?.count??0]].map(([label,value])=>
        <div key={String(label)} className="rounded-2xl border bg-card p-5 shadow-sm"><div className="text-sm text-muted-foreground">{label}</div><div className="mt-2 text-3xl font-black">{value}</div></div>)}
    </div>
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="rounded-2xl border bg-card shadow-sm"><div className="border-b p-4 font-semibold">{t("productsHome.priceLists")}</div><div className="divide-y">{priceLists.length?priceLists.map(p=><div key={p.id} className="flex items-center justify-between p-4"><div><div className="font-medium">{p.name}</div><div className="text-xs text-muted-foreground">{p.code} · {p.channel}</div></div><span className="text-sm">{p.currency}{p.is_default?` · ${t("productsHome.default")}`:""}</span></div>):<div className="p-6 text-sm text-muted-foreground">{t("productsHome.emptyPriceLists")}</div>}</div></div>
      <div className="rounded-2xl border bg-card shadow-sm"><div className="border-b p-4 font-semibold">{t("productsHome.recipeSku")}</div><div className="divide-y">{recipes.length?recipes.slice(0,12).map(r=><div key={r.id} className="p-4"><div className="flex items-center justify-between"><div className="font-medium">{r.name_ar}</div><span className="rounded-full bg-muted px-2 py-1 text-xs">{t("productsHome.skuCode")}: {r.code}</span></div><div className="mt-1 text-xs text-muted-foreground">{t("productsHome.version")} {r.version} · {t("productsHome.unitCost")} {r.cost_per_yield} · {r.lines.length} {t("productsHome.components")}</div></div>):<div className="p-6 text-sm text-muted-foreground">{t("productsHome.emptyRecipes")}</div>}</div></div>
    </div>
    <div className="rounded-2xl border bg-card shadow-sm"><div className="border-b p-4"><div className="font-semibold">{t("productsHome.pricingImpact")}</div><div className="text-xs text-muted-foreground">{t("productsHome.pricingImpactDescription")}</div></div>
      <div className="overflow-auto"><table className="w-full text-sm"><thead><tr className="border-b bg-muted/40"><th className="p-3 text-right">{t("productsHome.product")}</th><th className="p-3 text-right">{t("productsHome.cost")}</th><th className="p-3 text-right">{t("productsHome.price")}</th><th className="p-3 text-right">{t("productsHome.margin")}</th><th className="p-3 text-right">{t("productsHome.recommendedPrice")}</th></tr></thead><tbody>{(impact?.items??[]).slice(0,20).map(i=><tr key={i.product_id} className="border-b"><td className="p-3">{i.product_name}</td><td className="p-3">{i.current_cost}</td><td className="p-3">{i.sale_price}</td><td className="p-3">{i.gross_margin_percentage}%</td><td className="p-3">{i.recommended_price_at_margin??"—"}</td></tr>)}</tbody></table></div>
    </div></>}
  </section>;
}
