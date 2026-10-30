import { useTranslation } from "react-i18next";
import { Link } from "react-router-dom";

export default function InventoryPage() {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
  const areas = [
    { title: t("inventory.home.warehouses"), href: "/inventory/warehouses", description: t("inventory.home.warehousesDescription") },
    { title: t("inventory.home.locations"), href: "/inventory/locations", description: t("inventory.home.locationsDescription") },
    { title: t("inventory.home.items"), href: "/products", description: t("inventory.home.itemsDescription") },
  ];

  return (
    <section className="space-y-6 p-6" dir={direction}>
      <header>
        <h1 className="text-2xl font-bold">{t("inventory.home.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("inventory.home.description")}
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-3">
        {areas.map(({ title, href, description }) => (
          <Link key={href} to={href} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md">
            <h2 className="font-semibold">{title}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{description}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
