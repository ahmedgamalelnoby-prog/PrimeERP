import { useMemo, useState } from "react";
import { Boxes, Building2, Calculator, ChevronDown, CircleHelp, Headphones, LayoutGrid, Search, ShieldCheck, ShoppingCart, Users2 } from "lucide-react";
import { Input } from "@/components/ui/input";

type CatalogItem = { name: string; ar: string; description: string };
type CatalogGroup = { name: string; ar: string; icon: typeof LayoutGrid; items: CatalogItem[] };

const catalog: CatalogGroup[] = [
  { name: "Platform & Security", ar: "المنصة والأمان", icon: ShieldCheck, items: [
    { name: "Identity & Access", ar: "الهوية والصلاحيات", description: "Users, roles, permissions, authentication and access control." },
    { name: "Organizations", ar: "الشركات والفروع", description: "Companies, branches, tenant context and organizational structure." },
    { name: "SaaS Management", ar: "إدارة الـSaaS", description: "Plans, subscriptions, trials, entitlements and tenant lifecycle." },
    { name: "Audit", ar: "سجل التدقيق", description: "Track important changes and security-sensitive activities." },
    { name: "Approvals & Workflow", ar: "الموافقات وسير العمل", description: "Controlled approvals and configurable business workflows." },
    { name: "Notifications", ar: "الإشعارات", description: "Operational notifications and user-facing alerts." },
    { name: "Integrations", ar: "التكاملات", description: "Connect PrimeERP with external services and commerce providers." },
    { name: "Language", ar: "اللغات", description: "Arabic/English experience with RTL/LTR support." },
  ]},
  { name: "Finance", ar: "المالية", icon: Calculator, items: [
    { name: "Accounting", ar: "المحاسبة", description: "Chart of accounts, journals, entries, ledgers and financial reports." },
    { name: "Treasury", ar: "الخزينة والبنوك", description: "Cash, banks, receipts, payments, checks and transfers." },
    { name: "Invoicing & Transactions", ar: "الفواتير والمعاملات", description: "Sales/purchase invoices, transaction lifecycle and settlement." },
    { name: "Taxes", ar: "الضرائب", description: "Tax rules, rates and tax-aware transaction processing." },
    { name: "Egyptian E-Invoice", ar: "الفاتورة الإلكترونية المصرية", description: "ETA integration foundation for electronic documents." },
    { name: "Assets", ar: "الأصول", description: "Fixed assets, depreciation, movement and disposal." },
    { name: "Budgets & Cost Centers", ar: "الميزانيات ومراكز التكلفة", description: "Budget control, cost allocation and management analysis." },
    { name: "Expenses", ar: "المصروفات", description: "Capture and control business expenses and their accounting impact." },
  ]},
  { name: "Commercial", ar: "التجارة والمبيعات", icon: ShoppingCart, items: [
    { name: "CRM", ar: "إدارة علاقات العملاء", description: "Leads, opportunities, activities and sales pipeline." },
    { name: "Sales", ar: "المبيعات", description: "Quotations, orders, customers, pricing and sales invoices." },
    { name: "Purchasing", ar: "المشتريات", description: "Suppliers, purchase orders, receipts and vendor invoices." },
    { name: "POS", ar: "نقطة البيع", description: "Point-of-sale sessions, orders, payments and receipts." },
    { name: "Commerce", ar: "التجارة الإلكترونية", description: "Commerce workflows, products, orders and online operations." },
    { name: "Subscriptions", ar: "الاشتراكات", description: "Recurring services, billing cycles, renewals and cancellations." },
    { name: "Rentals", ar: "التأجير", description: "Rental contracts, periods, pricing, deposits and returns." },
    { name: "Loyalty & Promotions", ar: "الولاء والعروض", description: "Customer loyalty, promotions and commercial incentives." },
    { name: "Commissions", ar: "العمولات", description: "Sales commission rules, calculations and tracking." },
  ]},
  { name: "Supply Chain & Operations", ar: "سلاسل الإمداد والتشغيل", icon: Boxes, items: [
    { name: "Inventory", ar: "المخزون", description: "Products, warehouses, locations, transfers, adjustments and valuation." },
    { name: "Product Catalog", ar: "كتالوج المنتجات", description: "Products, variants, bundles, pricing and lifecycle." },
    { name: "UOM", ar: "وحدات القياس", description: "Units of measure and conversion rules." },
    { name: "Shipping", ar: "الشحن", description: "Delivery workflows, settlement and shipping accounting." },
    { name: "Manufacturing", ar: "التصنيع", description: "Manufacturing orders, production flows and material consumption." },
    { name: "Quality", ar: "الجودة", description: "Quality checks, inspections and operational controls." },
    { name: "Maintenance", ar: "الصيانة", description: "Maintenance requests, preventive schedules and equipment care." },
    { name: "Work Orders", ar: "أوامر العمل", description: "Operational work orders and execution tracking." },
  ]},
  { name: "Enterprise & People", ar: "المؤسسة والموارد البشرية", icon: Users2, items: [
    { name: "HR", ar: "الموارد البشرية", description: "Employee records, organizational roles and HR operations." },
    { name: "Attendance & Time", ar: "الحضور والوقت", description: "Attendance, working time and time tracking." },
    { name: "Payroll", ar: "الرواتب", description: "Salary structures, payroll runs, deductions and payslips." },
    { name: "Recruitment", ar: "التوظيف", description: "Vacancies, applicants, interviews and hiring workflow." },
    { name: "Projects", ar: "المشروعات", description: "Projects, tasks, milestones, dependencies and progress." },
    { name: "Enterprise", ar: "إدارة المؤسسة", description: "Enterprise-level assets, budgets, HR, projects and contracts." },
    { name: "Documents", ar: "المستندات", description: "Centralized business documents and linked records." },
    { name: "Legal", ar: "الشؤون القانونية", description: "Legal documents, policies and controlled records." },
  ]},
  { name: "Industry & Customer Service", ar: "القطاعات وخدمة العملاء", icon: Headphones, items: [
    { name: "Restaurant", ar: "المطاعم", description: "Restaurant operations, orders, tables and connected POS workflows." },
    { name: "Hotels / Hospitality", ar: "الفنادق والضيافة", description: "Hospitality operations and hotel revenue workflows." },
    { name: "Real Estate", ar: "العقارات", description: "Real-estate oriented operations and commercial workflows." },
    { name: "Help Desk + Prime AI", ar: "الدعم الفني + Prime AI", description: "AI answers customer questions about PrimeERP and guides users through workflows." },
    { name: "Reports & Analytics", ar: "التقارير والتحليلات", description: "Operational, financial and management reporting." },
    { name: "AI Business Analytics", ar: "تحليلات الأعمال بالـAI", description: "AI-assisted analysis of supplied ERP metrics and management questions." },
    { name: "Email / WhatsApp Reporting", ar: "إرسال التقارير", description: "Scheduled report delivery through configured email or WhatsApp channels." },
    { name: "Mobile", ar: "الموبايل", description: "Mobile-oriented application foundation and services." },
  ]},
];

export default function ModuleCatalogPage() {
  const [search, setSearch] = useState("");
  const [open, setOpen] = useState<string[]>(catalog.map(group => group.name));
  const normalized = search.trim().toLowerCase();
  const filtered = useMemo(() => catalog.map(group => ({ ...group, items: group.items.filter(item => !normalized || [item.name, item.ar, item.description].join(" ").toLowerCase().includes(normalized)) })).filter(group => group.items.length), [normalized]);
  const toggle = (name: string) => setOpen(current => current.includes(name) ? current.filter(item => item !== name) : [...current, name]);

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-slate-50 p-4 sm:p-6 lg:p-8" dir="rtl">
      <div className="mx-auto max-w-7xl">
        <div className="mb-7 rounded-3xl bg-slate-950 p-6 text-white shadow-xl sm:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div><div className="mb-3 inline-flex items-center gap-2 rounded-full bg-blue-500/10 px-3 py-1.5 text-xs font-bold text-blue-300"><LayoutGrid className="size-4" />PrimeERP Module Architecture</div><h1 className="text-3xl font-black sm:text-4xl">كتالوج PrimeERP الكامل</h1><p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">مرجع موحد لترتيب النظام والموديولات والخدمات. كل موديول له دور واضح ويمكن ربطه بالصلاحيات والباقات وسير العمل حسب احتياج الشركة.</p></div>
            <div className="flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-cyan-400"><Building2 className="size-8" /></div>
          </div>
        </div>
        <div className="mb-6 flex items-center gap-3 rounded-2xl border border-slate-200 bg-white p-3 shadow-sm"><Search className="size-5 text-slate-400" /><Input value={search} onChange={e => setSearch(e.target.value)} placeholder="ابحث عن موديول أو خدمة..." className="border-0 shadow-none focus-visible:ring-0" /><span className="text-xs font-bold text-slate-400">{filtered.reduce((sum, group) => sum + group.items.length, 0)} موديول</span></div>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map(group => { const Icon = group.icon; const expanded = open.includes(group.name); return <div key={group.name} className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm">
            <button type="button" onClick={() => toggle(group.name)} className="flex w-full items-center justify-between p-5 text-start hover:bg-slate-50"><div className="flex items-center gap-3"><div className="flex size-11 items-center justify-center rounded-xl bg-blue-50 text-blue-600"><Icon className="size-5" /></div><div><div className="font-black">{group.ar}</div><div className="text-xs text-slate-400">{group.name}</div></div></div><ChevronDown className={expanded ? "size-5 rotate-180 text-slate-400" : "size-5 text-slate-400"} /></button>
            {expanded && <div className="border-t border-slate-100 p-3">{group.items.map(item => <div key={item.name} className="rounded-2xl p-3 hover:bg-slate-50"><div className="flex items-start gap-3"><div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500"><CircleHelp className="size-4" /></div><div><div className="text-sm font-bold text-slate-800">{item.ar}</div><div className="text-[11px] font-semibold text-blue-600">{item.name}</div><p className="mt-1 text-xs leading-5 text-slate-500">{item.description}</p></div></div></div>)}</div>}
          </div>})}
        </div>
        {!filtered.length && <div className="rounded-3xl border border-dashed bg-white p-12 text-center text-sm text-slate-500">لا توجد نتائج مطابقة.</div>}
      </div>
    </div>
  );
}
