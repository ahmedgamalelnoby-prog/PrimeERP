import { Link } from "react-router-dom";

const areas = [
  ["المخازن", "/inventory/warehouses", "مخزن مركزي للشركة أو عدة مخازن لكل فرع"],
  ["مواقع التخزين", "/inventory/locations", "مواقع هرمية داخل كل مخزن: استلام وتخزين وشحن وغيرها"],
  ["الأصناف والمخزون", "/products", "دليل الأصناف والأرصدة والتكلفة"],
  ["حركات المخزون", "/inventory/transactions", "استلام وصرف وتحويل وتسويات ومرتجعات مع الترحيل والعكس"],
  ["تحويلات المخزون", "/inventory/transfers", "طلب واعتماد وشحن واستلام التحويل بين المخازن"],
  ["الحجوزات", "/inventory/reservations", "حجز وتحرير وإلغاء الكميات للطلبات وعمليات الـWMS"],
];

export default function InventoryPage() {
  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">المخزون والمستودعات</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          إدارة الشركات والفروع والمخزن المركزي ومخازن الفروع ومواقع التخزين من طبقة واحدة.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
        {areas.map(([title, href, description]) => (
          <Link key={href} to={href} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md">
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
