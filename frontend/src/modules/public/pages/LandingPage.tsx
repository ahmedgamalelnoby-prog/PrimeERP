import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const features = [
  {
    title: "الحسابات",
    description: "إدارة القيود والحسابات والتقارير المالية من مكان واحد.",
  },
  {
    title: "المبيعات",
    description: "تابع العملاء وعروض الأسعار وطلبات وفواتير المبيعات.",
  },
  {
    title: "المخزون",
    description: "تحكم في المنتجات والمخازن والأرصدة وحركات المخزون.",
  },
  {
    title: "الموارد البشرية",
    description: "نظّم بيانات الموظفين والحضور والإجازات والرواتب.",
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground" dir="rtl">
      <header className="sticky top-0 z-50 border-b bg-background/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link to="/" className="text-2xl font-extrabold tracking-tight">
            Prime<span className="text-primary">ERP</span>
          </Link>

          <nav className="hidden items-center gap-7 text-sm font-medium md:flex">
            <a href="#features" className="hover:text-primary">
              المنتجات
            </a>
            <a href="#industries" className="hover:text-primary">
              القطاعات
            </a>
            <Link to="/pricing" className="hover:text-primary">
              الأسعار
            </Link>
            <a href="#help" className="hover:text-primary">
              المساعدة
            </a>
          </nav>

          <div className="flex items-center gap-2">
            <Button variant="ghost" asChild>
              <Link to="/login">تسجيل الدخول</Link>
            </Button>

            <Button asChild>
              <Link to="/register">ابدأ مجانًا</Link>
            </Button>
          </div>
        </div>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="mx-auto grid min-h-[680px] max-w-7xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:px-8">
            <div>
              <div className="mb-5 inline-flex rounded-full border bg-muted px-4 py-2 text-sm">
                منصة ERP سحابية متكاملة
              </div>

              <h1 className="max-w-3xl text-4xl font-extrabold leading-tight sm:text-5xl lg:text-6xl">
                إدارة شركتك بالكامل
                <span className="block text-primary">من مكان واحد</span>
              </h1>

              <p className="mt-6 max-w-2xl text-lg leading-8 text-muted-foreground">
                PrimeERP Cloud يساعدك على إدارة الحسابات والمبيعات والمخزون
                والموارد البشرية والعمليات من خلال منصة واحدة سهلة وآمنة.
              </p>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <Button size="lg" asChild>
                  <Link to="/register">ابدأ مجانًا لمدة 14 يومًا</Link>
                </Button>

                <Button size="lg" variant="outline" asChild>
                  <Link to="/login">تسجيل الدخول</Link>
                </Button>
              </div>

              <p className="mt-4 text-sm text-muted-foreground">
                لا تحتاج إلى بطاقة بنكية لبدء التجربة.
              </p>
            </div>

            <Card className="overflow-hidden border-2 shadow-2xl">
              <CardContent className="p-0">
                <div className="border-b bg-muted/50 p-4">
                  <div className="flex gap-2">
                    <span className="h-3 w-3 rounded-full bg-muted-foreground/30" />
                    <span className="h-3 w-3 rounded-full bg-muted-foreground/30" />
                    <span className="h-3 w-3 rounded-full bg-muted-foreground/30" />
                  </div>
                </div>

                <div className="grid min-h-[390px] grid-cols-[90px_1fr]">
                  <div className="border-l bg-muted/40 p-3">
                    <div className="mb-5 h-8 rounded bg-primary/20" />
                    {Array.from({ length: 6 }).map((_, index) => (
                      <div
                        key={index}
                        className="mb-3 h-7 rounded bg-muted-foreground/10"
                      />
                    ))}
                  </div>

                  <div className="p-6">
                    <h2 className="text-xl font-bold">لوحة التحكم</h2>
                    <p className="mt-1 text-sm text-muted-foreground">
                      ملخص أداء شركتك
                    </p>

                    <div className="mt-6 grid grid-cols-2 gap-4">
                      {["الإيرادات", "المصروفات", "العملاء", "الفواتير"].map(
                        (item) => (
                          <div key={item} className="rounded-xl border p-4">
                            <p className="text-sm text-muted-foreground">
                              {item}
                            </p>
                            <div className="mt-3 h-7 w-24 rounded bg-primary/20" />
                          </div>
                        ),
                      )}
                    </div>

                    <div className="mt-5 h-32 rounded-xl border bg-muted/30 p-4">
                      <div className="flex h-full items-end gap-3">
                        {[40, 70, 55, 90, 65, 82].map((height, index) => (
                          <div
                            key={index}
                            className="flex-1 rounded-t bg-primary/40"
                            style={{ height: `${height}%` }}
                          />
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>

        <section id="features" className="border-y bg-muted/30 py-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold">
                كل ما تحتاجه لإدارة شركتك
              </h2>
              <p className="mt-4 text-muted-foreground">
                وحدات مترابطة تعمل معًا وتمنحك رؤية كاملة لأعمالك.
              </p>
            </div>

            <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <Card key={feature.title}>
                  <CardContent className="p-6">
                    <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 font-bold text-primary">
                      {feature.title.charAt(0)}
                    </div>
                    <h3 className="text-lg font-bold">{feature.title}</h3>
                    <p className="mt-2 text-sm leading-6 text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        <section id="industries" className="py-20">
          <div className="mx-auto max-w-7xl px-4 text-center sm:px-6 lg:px-8">
            <h2 className="text-3xl font-bold">مصمم لمختلف القطاعات</h2>
            <p className="mx-auto mt-4 max-w-2xl text-muted-foreground">
              شركات التجارة والمطاعم والفنادق والعقارات والخدمات يمكنها تشغيل
              أعمالها من خلال PrimeERP.
            </p>
          </div>
        </section>

        <section className="bg-primary py-16 text-primary-foreground">
          <div className="mx-auto max-w-4xl px-4 text-center">
            <h2 className="text-3xl font-bold">
              ابدأ بناء شركتك الرقمية اليوم
            </h2>
            <p className="mt-4 opacity-90">
              جرّب PrimeERP Cloud مجانًا لمدة 14 يومًا.
            </p>
            <Button className="mt-7" size="lg" variant="secondary" asChild>
              <Link to="/register">ابدأ التجربة المجانية</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer id="help" className="border-t py-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 text-sm text-muted-foreground sm:px-6 md:flex-row md:items-center md:justify-between lg:px-8">
          <p>© 2026 PrimeERP Cloud. جميع الحقوق محفوظة.</p>
          <div className="flex gap-5">
            <Link to="/pricing">الأسعار</Link>
            <Link to="/login">تسجيل الدخول</Link>
            <Link to="/register">ابدأ مجانًا</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
