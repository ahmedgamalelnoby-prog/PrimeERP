import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Settings, Building2, Calculator, ShoppingCart, Boxes, Users, Workflow,
  MessageCircle, BarChart3, Plug, Receipt, Store, Factory, UserRound,
  ChevronDown, SlidersHorizontal, Check, type LucideIcon,
} from "lucide-react";
import { useTranslation } from "react-i18next";
import SettingsPage from "./SettingsPage";
import CompanyPolicySettingsPage from "./CompanyPolicySettingsPage";

type SettingsSection = {
  id: string;
  title: string;
  english: string;
  desc: string;
  icon: LucideIcon;
};

const sections: SettingsSection[] = [
  { id: "General", title: "الإعدادات العامة", english: "General", desc: "بيانات الشركة واللغة والتاريخ والمنطقة الزمنية والعملة.", icon: Building2 },
  { id: "Accounting", title: "المحاسبة", english: "Accounting", desc: "الفترات المالية والحسابات وسياسات الترحيل.", icon: Calculator },
  { id: "Taxes", title: "الضرائب والفاتورة الإلكترونية", english: "Taxes & e-Invoicing", desc: "الضرائب والإقرارات والفوترة الإلكترونية.", icon: Receipt },
  { id: "Sales", title: "المبيعات والعملاء", english: "Sales & Customers", desc: "التسعير والخصومات والائتمان والمبيعات.", icon: ShoppingCart },
  { id: "Purchasing", title: "المشتريات والموردون", english: "Purchasing & Suppliers", desc: "المشتريات والاعتمادات وسياسات الموردين.", icon: Store },
  { id: "Inventory", title: "المخزون والمستودعات", english: "Inventory & Warehouses", desc: "التقييم والحجز والجرد وإعادة الطلب.", icon: Boxes },
  { id: "Human Resources", title: "الموارد البشرية والحضور والرواتب", english: "HR, Attendance & Payroll", desc: "البصمة والحضور والإجازات والرواتب والاعتماد.", icon: Users },
  { id: "Approvals", title: "الموافقات وسير العمل", english: "Approvals & Workflow", desc: "مسارات الاعتماد والتفويض والتصعيد.", icon: Workflow },
  { id: "Point of Sale", title: "نقاط البيع ودرج النقدية", english: "POS & Cash Drawer", desc: "إعدادات نقاط البيع والوردية ودرج النقدية.", icon: Store },
  { id: "Manufacturing", title: "التصنيع", english: "Manufacturing", desc: "أوامر الإنتاج وقوائم المواد والتكاليف.", icon: Factory },
  { id: "CRM", title: "إدارة العملاء", english: "CRM", desc: "مراحل الفرص والعملاء والمتابعة.", icon: UserRound },
  { id: "Integrations", title: "التكاملات الخارجية", english: "Integrations", desc: "الأنظمة الخارجية والربط والمزامنة.", icon: Plug },
  { id: "Messaging & Notifications", title: "الرسائل وWhatsApp", english: "Messages & WhatsApp", desc: "قوالب الرسائل والمجموعات والتنبيهات.", icon: MessageCircle },
  { id: "Reporting", title: "التقارير والتصدير", english: "Reports & Export", desc: "خيارات التقارير والتصدير والجدولة.", icon: BarChart3 },
];

export default function SettingsCenterPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { i18n, t } = useTranslation();
  const isArabic = i18n.resolvedLanguage?.startsWith("ar") ?? true;
  const activeId = searchParams.get("category") || "General";
  const selected = useMemo(
    () => sections.find((section) => section.id === activeId) ?? sections[0],
    [activeId],
  );
  const [expandedId, setExpandedId] = useState<string>(selected.id);
  const Icon = selected.icon;

  useEffect(() => {
    setExpandedId(selected.id);
  }, [selected.id]);

  const selectSection = (id: string) => {
    setSearchParams({ category: id }, { replace: false });
    setExpandedId(id);
  };

  const toggleSection = (id: string) => {
    if (expandedId === id) {
      setExpandedId("");
      return;
    }
    selectSection(id);
  };

  return (
    <div className="mx-auto w-full max-w-[1700px] space-y-4 rounded-2xl bg-[#f3f7f6] p-2 sm:p-4" dir={isArabic ? "rtl" : "ltr"}>
      <header className="flex min-h-[76px] flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#e4eceb] bg-white px-5 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="flex size-11 items-center justify-center rounded-xl bg-[#e7f7f3] text-[#087f73]">
            <Settings className="size-5" />
          </span>
          <div>
            <p className="text-xs font-semibold text-muted-foreground">PrimeERP · {t("settingsCenter.controlCenter")}</p>
            <h1 className="mt-0.5 text-xl font-black">{t("settingsCenter.title")}</h1>
          </div>
        </div>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
          {t("settingsCenter.description")}
        </p>
      </header>

      <div className={["grid min-h-[72vh] gap-4", isArabic ? "lg:grid-cols-[286px_minmax(0,1fr)]" : "lg:grid-cols-[minmax(0,1fr)_286px]"].join(" ")}>
        <aside className="flex h-fit flex-col overflow-hidden rounded-[18px] border border-[#102b38] bg-[#102b38] text-[#d8e7e8] shadow-sm lg:sticky lg:top-24 lg:max-h-[calc(100vh-7rem)]">
          <div className="border-b border-white/10 px-4 py-5">
            <div className="flex items-center gap-3">
              <span className="flex size-9 items-center justify-center rounded-xl bg-[#18a998]">
                <SlidersHorizontal className="size-4 text-white" />
              </span>
              <div>
                <h2 className="text-sm font-extrabold">{t("settingsCenter.moduleSettings")}</h2>
                <p className="mt-0.5 text-[11px] text-[#a9c6c7]">{t("settingsCenter.selectModule")}</p>
              </div>
            </div>
          </div>

          <nav aria-label={t("settingsCenter.settingsModules")} className="min-h-0 space-y-1 overflow-y-auto p-3 [scrollbar-color:rgba(148,163,184,.25)_transparent] [scrollbar-width:thin]">
            {sections.map((section) => {
              const SectionIcon = section.icon;
              const isExpanded = expandedId === section.id;
              const isActive = selected.id === section.id;
              return (
                <div key={section.id} className="space-y-1">
                  <button
                    type="button"
                    aria-expanded={isExpanded}
                    aria-controls={`settings-module-panel-${section.id.replace(/[^a-z0-9]/gi, "-")}`}
                    onClick={() => toggleSection(section.id)}
                    className={[
                      "group flex w-full items-center justify-between gap-3 rounded-[11px] px-3 py-3 text-start text-sm font-semibold transition-colors",
                      isActive
                        ? "bg-gradient-to-l from-cyan-400/20 to-blue-500/20 text-white ring-1 ring-inset ring-cyan-300/25"
                        : "text-slate-300 hover:bg-white/[0.07] hover:text-white",
                    ].join(" ")}
                  >
                    <span className="flex min-w-0 items-center gap-3">
                      <SectionIcon className={["size-[18px] shrink-0", isActive ? "text-[#18c4b0]" : "text-[#a9c6c7] group-hover:text-white"].join(" ")} />
                      <span className="min-w-0 flex-1">{t(`settingsCenter.sections.${section.id}.title`)}</span>
                    </span>
                    <ChevronDown className={["size-4 shrink-0 text-slate-500 transition-transform", isExpanded ? "rotate-180" : ""].join(" ")} />
                  </button>
                  {isExpanded && (
                    <div
                      id={`settings-module-panel-${section.id.replace(/[^a-z0-9]/gi, "-")}`}
                      className={["mx-3 rounded-lg border border-white/10 bg-[#1c414d] px-3 py-3", isArabic ? "mr-7" : "ml-7"].join(" ")}
                    >
                      <button
                        type="button"
                        onClick={() => selectSection(section.id)}
                        className="flex w-full items-center gap-2 text-start text-xs font-semibold text-[#8ce3d7] hover:text-white"
                      >
                        <Check className="size-3.5 shrink-0" />
                        <span>{t("settingsCenter.sectionSettings", { title: t(`settingsCenter.sections.${section.id}.title`) })}</span>
                      </button>
                      <p className="mt-2 text-[11px] leading-5 text-[#b4ced0]">{t(`settingsCenter.sections.${section.id}.description`)}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </nav>
          <div className="border-t border-white/10 px-4 py-3 text-center text-[10px] tracking-wide text-[#a9c6c7]">{t("settingsCenter.footer")}</div>
        </aside>

        <section className="min-w-0 rounded-[18px] border border-[#e4eceb] bg-white p-4 shadow-[0_8px_28px_rgba(17,53,59,.035)] sm:p-7">
          <div className="mb-5 flex flex-wrap items-start gap-3 border-b pb-4">
            <span className="rounded-xl bg-[#e8f7f3] p-3 text-[#0d9888]"><Icon className="size-5" /></span>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-extrabold">{t(`settingsCenter.sections.${selected.id}.title`)}</h2>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">{t(`settingsCenter.sections.${selected.id}.description`)}</p>
            </div>
            <span className="rounded-full border border-[#cdece5] bg-[#e7f7f3] px-3 py-1 text-[11px] font-semibold text-[#087f73]">
              {t("settingsCenter.moduleSettings")}
            </span>
          </div>
          <div className="min-w-0">
            {selected.id === "General" ? (
              <>
                <SettingsPage />
                <CompanyPolicySettingsPage key={selected.id} categoryFilter={selected.id} />
              </>
            ) : (
              <CompanyPolicySettingsPage key={selected.id} categoryFilter={selected.id} />
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
