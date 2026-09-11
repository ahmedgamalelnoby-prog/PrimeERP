import { Link } from 'react-router-dom';
const cards=[
 ['العملاء والموردون','/customers','دليل موحد للعملاء والموردين وشروط الائتمان والضرائب.'],
 ['عروض المبيعات','/sales/quotations','Quotation → Order → Delivery → Invoice → Payment.'],
 ['طلبات المبيعات','/sales/orders','دورة المبيعات كاملة مع ربط المخزون والشحن.'],
 ['المشتريات','/purchases/orders','RFQ → Purchase Order → Receipt → Bill → Payment.'],
 ['الشحن واللوجستيات','/shipping','شركات الشحن، طرق الدفع، COD، التتبع وحالات الشحنة.'],
 ['الضرائب','/accounting','VAT و WHT وقواعد الضرائب قابلة للتوسع.'],
];
export default function CommercePage(){return <section className="space-y-6 p-6" dir="rtl"><header><h1 className="text-2xl font-bold">المبيعات والمشتريات</h1><p className="mt-1 text-sm text-muted-foreground">طبقة التجارة المتكاملة من المستند الأول حتى المخزون والفاتورة والتحصيل أو السداد.</p></header><div className="grid gap-4 md:grid-cols-3">{cards.map(([title,href,desc])=><Link key={href} to={href} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md"><h2 className="font-semibold">{title}</h2><p className="mt-2 text-sm text-muted-foreground">{desc}</p></Link>)}</div></section>}
