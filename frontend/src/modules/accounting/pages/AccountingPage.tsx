import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export default function AccountingPage() {
  const { t, i18n } = useTranslation();
  const areas = [
    ["chartOfAccounts", "/accounting/chart-of-accounts"],
    ["journalEntries", "/accounting/journal-entries"],
    ["financialReports", "/accounting/reports"],
    ["arApAging", "/accounting/ar-ap-aging"],
    ["partnerStatements", "/accounting/partner-statements"],
  ];
  return (
    <section className="space-y-6 p-6" dir={i18n.dir()}>
      <header>
        <h1 className="text-2xl font-bold">{t("accountingHome.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">{t("accountingHome.description")}</p>
      </header>
      <div className="grid gap-4 md:grid-cols-3">
        {areas.map(([key, href]) => (
          <Link key={href} to={href} className="rounded-2xl border bg-card p-5 shadow-sm transition hover:shadow-md">
            <h2 className="font-semibold">{t(`accountingHome.areas.${key}.title`)}</h2>
            <p className="mt-2 text-sm text-muted-foreground">{t(`accountingHome.areas.${key}.description`)}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
