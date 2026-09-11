import { Link } from "react-router-dom";

const areas = [
  ["الأصول الثابتة", "/enterprise/assets", "الأصول، الإهلاك، القيمة الدفترية والتصرف.", "Assets"],
  ["الموازنات", "/enterprise/budgets", "الموازنة والاعتماد ومتابعة الانحراف.", "Budgets"],
  ["الموظفون والرواتب", "/enterprise/hr", "ملفات الموظفين وتشغيل Payroll.", "HR & Payroll"],
  ["المشروعات", "/enterprise/projects", "المشروعات والتكلفة ومتابعة التنفيذ.", "Projects"],
  ["العقود", "/enterprise/contracts", "عقود المشروعات والقيم والاستقطاعات.", "Contracts"],
] as const;

export default function EnterprisePage() {
  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header className="space-y-1">
        <h1 className="text-2xl font-bold">عمليات المؤسسة</h1>
        <p className="text-sm text-muted-foreground">اختر المجال التشغيلي المطلوب. كل مجال يعمل كـ Module مستقل ويرتبط بالبيانات المشتركة فقط عند الحاجة.</p>
      </header>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {areas.map(([title, href, description, english]) => (
          <Link key={href} to={href} className="group rounded-2xl border bg-card p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
            <div className="flex items-start justify-between gap-3">
              <h2 className="font-semibold">{title}</h2>
              <span className="rounded-full bg-muted px-2 py-1 text-[10px] text-muted-foreground">{english}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-muted-foreground">{description}</p>
            <span className="mt-4 inline-flex text-sm font-medium text-primary">فتح الوحدة ←</span>
          </Link>
        ))}
      </div>
    </section>
  );
}
