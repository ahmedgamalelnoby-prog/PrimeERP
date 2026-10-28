import type { LucideIcon } from "lucide-react";
import { BadgeDollarSign, Banknote, BarChart3, Bell, Boxes, Building2, Calculator, CalendarRange, CheckSquare, ClipboardCheck, Contact, FileCheck2, FileText, Gauge, Hotel, Landmark, LayoutDashboard, Package, Settings, ShieldCheck, SlidersHorizontal, ShoppingCart, Store, Truck, UserCog, Users, UsersRound, Wallet, Warehouse } from "lucide-react";

export type NavigationItemType = "item" | "group" | "separator";
export interface NavigationItem { id:string; label:string; labelAr:string; type:NavigationItemType; path?:string; icon?:LucideIcon; children?:NavigationItem[]; permission?:string; module?:string; visible?:boolean; disabled?:boolean; isNew?:boolean; comingSoon?:boolean; order?:number; }

export const navigationItems: NavigationItem[] = [
 {id:"dashboard",label:"Dashboard",labelAr:"لوحة التحكم",type:"item",path:"/dashboard",icon:LayoutDashboard,module:"dashboard",visible:true,order:1},
 {id:"module-catalog",label:"Module Catalog",labelAr:"كتالوج الموديولات",type:"item",path:"/modules",icon:Boxes,module:"platform",visible:true,isNew:true,order:2},
 {id:"helpdesk",label:"AI Help Desk",labelAr:"الدعم الفني بالـAI",type:"item",path:"/helpdesk",icon:Contact,module:"helpdesk",visible:true,isNew:true,order:3},
 {id:"identity",label:"Identity & Access",labelAr:"المستخدمون والصلاحيات",type:"group",icon:ShieldCheck,module:"identity",visible:true,order:4,children:[
  {id:"users",label:"Users",labelAr:"المستخدمون",type:"item",path:"/identity/users",icon:Users,permission:"users.access",module:"identity",visible:true,order:1},
  {id:"roles",label:"Roles",labelAr:"الأدوار",type:"item",path:"/identity/roles",icon:UserCog,permission:"roles.view",module:"identity",visible:true,order:2},
  {id:"permissions",label:"Permissions",labelAr:"الصلاحيات",type:"item",path:"/identity/permissions",icon:CheckSquare,permission:"permissions.view",module:"identity",visible:true,order:3}]},
 {id:"organization",label:"Organization",labelAr:"إدارة المؤسسة",type:"group",icon:Building2,module:"organization",visible:true,order:5,children:[
  {id:"companies",label:"Companies",labelAr:"الشركات",type:"item",path:"/companies",icon:Building2,permission:"companies.view",module:"organization",visible:true,order:1},
  {id:"branches",label:"Branches",labelAr:"الفروع",type:"item",path:"/branches",icon:Store,permission:"branches.view",module:"organization",visible:true,order:2}]},
 {id:"accounting",label:"Accounting",labelAr:"الحسابات العامة",type:"group",icon:Calculator,module:"accounting",visible:true,order:6,children:[
  {id:"chart-of-accounts",label:"Chart of Accounts",labelAr:"دليل الحسابات",type:"item",path:"/accounting/chart-of-accounts",icon:BarChart3,permission:"chart_of_accounts.view",module:"accounting",visible:true,order:1},
  {id:"fiscal-years",label:"Fiscal Years",labelAr:"السنوات المالية",type:"item",path:"/accounting/fiscal-years",icon:CalendarRange,permission:"fiscal_years.view",module:"accounting",visible:true,order:2},
  {id:"journals",label:"Journals",labelAr:"دفاتر اليومية",type:"item",path:"/accounting/journals",icon:FileText,permission:"journals.view",module:"accounting",visible:true,order:3},
  {id:"journal-entries",label:"Journal Entries",labelAr:"القيود اليومية",type:"item",path:"/accounting/journal-entries",icon:FileText,permission:"journal_entries.view",module:"accounting",visible:true,order:4},
  {id:"cost-centers",label:"Cost Centers",labelAr:"مراكز التكلفة",type:"item",path:"/accounting/cost-centers",icon:Gauge,permission:"cost_centers.view",module:"accounting",visible:true,order:5},
  {id:"financial-reports",label:"Financial Reports",labelAr:"التقارير المالية",type:"item",path:"/reports",icon:BarChart3,permission:"reports.view",module:"reports",visible:true,order:6}]},
 {id:"treasury",label:"Treasury",labelAr:"الخزينة والبنوك",type:"group",icon:Landmark,module:"treasury",visible:true,order:7,children:[
  {id:"banks",label:"Banks",labelAr:"البنوك",type:"item",path:"/treasury/banks",icon:Landmark,permission:"banks.view",module:"treasury",visible:true,order:1},
  {id:"cash",label:"Cash",labelAr:"الخزن النقدية",type:"item",path:"/treasury/cash",icon:Banknote,permission:"cash.view",module:"treasury",visible:true,order:2},
  {id:"checks",label:"Checks",labelAr:"الشيكات",type:"item",path:"/treasury/checks",icon:Wallet,permission:"checks.view",module:"treasury",visible:true,order:3}]},
 {id:"sales",label:"Sales",labelAr:"المبيعات",type:"group",icon:ShoppingCart,module:"sales",visible:true,order:8,children:[
  {id:"customers",label:"Customers",labelAr:"العملاء",type:"item",path:"/customers",icon:UsersRound,permission:"customers.view",module:"sales",visible:true,order:1},
  {id:"sales-orders",label:"Sales Orders",labelAr:"أوامر البيع",type:"item",path:"/sales/orders",icon:FileCheck2,permission:"sales_orders.view",module:"sales",visible:true,order:2},
  {id:"sales-invoices",label:"Sales Invoices",labelAr:"فواتير المبيعات",type:"item",path:"/sales/invoices",icon:FileText,permission:"sales_invoices.view",module:"sales",visible:true,order:3}]},
 {id:"purchasing",label:"Purchasing",labelAr:"المشتريات",type:"group",icon:Truck,module:"purchasing",visible:true,order:9,children:[
  {id:"suppliers",label:"Suppliers",labelAr:"الموردون",type:"item",path:"/purchasing/suppliers",icon:Contact,permission:"suppliers.view",module:"purchasing",visible:true,order:1},
  {id:"purchase-orders",label:"Purchase Orders",labelAr:"أوامر الشراء",type:"item",path:"/purchases/orders",icon:ClipboardCheck,permission:"purchase_orders.view",module:"purchasing",visible:true,order:2},
  {id:"purchase-invoices",label:"Purchase Invoices",labelAr:"فواتير المشتريات",type:"item",path:"/purchasing/invoices",icon:FileText,permission:"purchase_invoices.view",module:"purchasing",visible:true,order:3}]},
 {id:"inventory",label:"Inventory",labelAr:"المخزون",type:"group",icon:Boxes,module:"inventory",visible:true,order:10,children:[
  {id:"warehouses",label:"Warehouses",labelAr:"المخازن",type:"item",path:"/inventory/warehouses",icon:Warehouse,permission:"warehouses.view",module:"inventory",visible:true,order:1},
  {id:"locations",label:"Locations",labelAr:"مواقع التخزين",type:"item",path:"/inventory/locations",icon:Warehouse,permission:"locations.view",module:"inventory",visible:true,order:2},
  {id:"products",label:"Products",labelAr:"الأصناف",type:"item",path:"/products",icon:Package,permission:"products.view",module:"inventory",visible:true,order:3},
  {id:"stock-transactions",label:"Stock Transactions",labelAr:"حركات المخزون",type:"item",path:"/inventory/transactions",icon:Boxes,permission:"stock_transactions.view",module:"inventory",visible:true,order:4},
  {id:"transfers",label:"Transfers",labelAr:"تحويلات المخزون",type:"item",path:"/inventory/transfers",icon:Truck,permission:"inventory.write",module:"inventory",visible:true,order:5},
  {id:"reservations",label:"Reservations",labelAr:"حجوزات المخزون",type:"item",path:"/inventory/reservations",icon:ClipboardCheck,permission:"inventory.access",module:"inventory",visible:true,order:6}]},
 {id:"commercial-leasing",label:"Commercial Leasing",labelAr:"الإيجارات التجارية",type:"group",icon:Banknote,module:"commercial_leasing",visible:true,order:11,children:[
  {id:"lease-contracts",label:"Lease Contracts",labelAr:"عقود الإيجار",type:"item",path:"/commercial-leasing/contracts",icon:FileText,permission:"lease_contracts.view",module:"commercial_leasing",visible:true,order:1},
  {id:"installments",label:"Installments",labelAr:"الاستحقاقات",type:"item",path:"/commercial-leasing/installments",icon:BadgeDollarSign,permission:"installments.view",module:"commercial_leasing",visible:true,order:2},
  {id:"revenue-share",label:"Revenue Share",labelAr:"نسب الإيرادات",type:"item",path:"/commercial-leasing/revenue-share",icon:BarChart3,permission:"revenue_share.view",module:"commercial_leasing",visible:true,order:3}]},
 {id:"hospitality",label:"Hospitality",labelAr:"إدارة الفنادق",type:"group",icon:Hotel,module:"hospitality",visible:true,order:12,children:[
  {id:"hotels",label:"Hotels",labelAr:"الفنادق",type:"item",path:"/hospitality/hotels",icon:Hotel,permission:"hotels.view",module:"hospitality",visible:true,order:1},
  {id:"hotel-revenue",label:"Hotel Revenue",labelAr:"إيرادات الفنادق",type:"item",path:"/hospitality/revenue",icon:BadgeDollarSign,permission:"hotel_revenue.view",module:"hospitality",visible:true,order:2},
  {id:"hotel-profit-share",label:"Profit Share",labelAr:"نسب الأرباح",type:"item",path:"/hospitality/profit-share",icon:BarChart3,permission:"hotel_profit_share.view",module:"hospitality",visible:true,order:3}]},
 {id:"shipping",label:"Shipping",labelAr:"الشحن",type:"group",icon:Truck,module:"shipping",visible:true,order:13,children:[{id:"shipping-status-settings",label:"Status Settings",labelAr:"إعدادات حالات الشحن",type:"item",path:"/shipping/settings",icon:Settings,permission:"shipping.access",module:"shipping",visible:true,order:1},{id:"shipping-pricing",label:"Carrier Pricing",labelAr:"تسعير شركات الشحن",type:"item",path:"/shipping/pricing",icon:Calculator,permission:"shipping.access",module:"shipping",visible:true,order:2},{id:"shipping-settlements",label:"Settlements",labelAr:"تسويات شركات الشحن",type:"item",path:"/shipping/settlements",icon:Wallet,permission:"shipping.access",module:"shipping",visible:true,order:3},]},
 {id:"saas",label:"SaaS Administration",labelAr:"منصة SaaS",type:"group",icon:BadgeDollarSign,module:"saas",visible:true,order:14,children:[
  {id:"saas-dashboard",label:"SaaS Overview",labelAr:"نظرة عامة",type:"item",path:"/saas",icon:Gauge,module:"saas",visible:true,order:1,isNew:true},
  {id:"plans",label:"Plans & Entitlements",labelAr:"الباقات والاستحقاقات",type:"item",path:"/platform/plans",icon:BadgeDollarSign,permission:"plans.view",module:"saas",visible:true,order:2},
 ]},
 {id:"crm",label:"CRM",labelAr:"إدارة العملاء",type:"item",path:"/crm",icon:Contact,permission:"crm.view",module:"crm",visible:true,order:13},
 {id:"hr",label:"Human Resources",labelAr:"الموارد البشرية",type:"item",path:"/hr",icon:Users,permission:"hr.view",module:"hr",visible:true,order:13},
 {id:"pos",label:"Point of Sale",labelAr:"نقطة البيع",type:"item",path:"/pos",icon:Store,permission:"pos.view",module:"pos",visible:true,order:13},
 {id:"manufacturing",label:"Manufacturing",labelAr:"التصنيع",type:"item",path:"/manufacturing",icon:Boxes,permission:"manufacturing.view",module:"manufacturing",visible:true,order:13},
 {id:"commerce",label:"Commerce",labelAr:"التجارة",type:"item",path:"/commerce",icon:ShoppingCart,permission:"commerce.view",module:"commerce",visible:true,order:13},
 {id:"mobile",label:"Mobile",labelAr:"الموبايل",type:"item",path:"/mobile",icon:Package,permission:"mobile.view",module:"mobile",visible:true,order:13},
 {id:"reports",label:"Reports",labelAr:"التقارير",type:"item",path:"/reports",icon:BarChart3,permission:"reports.view",module:"reports",visible:true,order:14},
 {id:"notifications",label:"Messages & Notifications",labelAr:"الرسائل والإشعارات",type:"item",path:"/notifications",icon:Bell,permission:"company.write",module:"settings",visible:true,order:14},
 {id:"settings",label:"Settings",labelAr:"الإعدادات",type:"item",path:"/settings/center",icon:Settings,permission:"settings.view",module:"settings",visible:true,order:15},
 {id:"company-policies",label:"Company Policies",labelAr:"سياسات الشركة",type:"item",path:"/settings/company-policies",icon:SlidersHorizontal,permission:"company.write",module:"settings",visible:true,order:16},
];

const TENANT_CORE_NAVIGATION = new Set(["dashboard", "users", "companies", "branches", "settings", "company-policies", "helpdesk", "notifications"]);

function isNavigationAllowed(item: NavigationItem, enabledModules: Set<string>, grantedNames: Set<string>, isPlatformAdmin: boolean): boolean {
  if (isPlatformAdmin) return true;
  if (item.permission && !grantedNames.has(item.permission.toLowerCase())) return false;
  if (TENANT_CORE_NAVIGATION.has(item.id)) return true;
  if (item.id === "module-catalog" || item.id === "saas") return false;
  if (item.id === "reports") return enabledModules.has("reports");
  if (item.id === "identity" || item.id === "users" || item.id === "roles" || item.id === "permissions") return enabledModules.has("users");
  if (item.id === "organization" || item.id === "companies" || item.id === "branches") return enabledModules.has("companies") || enabledModules.has("branches");
  if (item.module) return enabledModules.has(item.module);
  return true;
}

export function getVisibleNavigationItems(enabledModuleCodes: string[] = [], isPlatformAdmin = false, permissionNames: string[] = []): NavigationItem[] {
  const enabledModules = new Set(enabledModuleCodes.map((code) => code.trim().toLowerCase()).filter(Boolean));
  const grantedNames = new Set(permissionNames.map((name) => name.trim().toLowerCase()).filter(Boolean));
  return navigationItems
    .filter((item) => item.visible !== false && isNavigationAllowed(item, enabledModules, grantedNames, isPlatformAdmin))
    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
    .map((item) => ({
      ...item,
      children: item.children
        ?.filter((child) => child.visible !== false && isNavigationAllowed(child, enabledModules, grantedNames, isPlatformAdmin))
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0)),
    }))
    .filter((item) => item.type !== "group" || Boolean(item.children?.length));
}

export function findNavigationItemByPath(
  path: string,
  items: NavigationItem[] = navigationItems,
): NavigationItem | undefined {
  for (const item of items) {
    if (item.path === path) return item;
    if (item.children?.length) {
      const child = findNavigationItemByPath(path, item.children);
      if (child) return child;
    }
  }
  return undefined;
}

export function findNavigationParent(path: string): NavigationItem | undefined {
  return navigationItems.find((item) =>
    item.children?.some((child) => child.path === path),
  );
}

export function flattenNavigationItems(
  items: NavigationItem[] = navigationItems,
): NavigationItem[] {
  return items.flatMap((item) => [
    item,
    ...(item.children ? flattenNavigationItems(item.children) : []),
  ]);
}

export function isNavigationItemActive(
  item: NavigationItem,
  pathname: string,
): boolean {
  if (item.path) {
    if (item.path === "/dashboard") return pathname === item.path;
    return pathname === item.path || pathname.startsWith(item.path + "/");
  }
  return item.children?.some((child) =>
    isNavigationItemActive(child, pathname),
  ) ?? false;
}
