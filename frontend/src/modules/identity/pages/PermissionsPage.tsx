import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import client from "@/shared/api/client";

type Permission = {
  id: number;
  name: string;
  resource: string;
  action: string;
  description: string | null;
  is_active: boolean;
};

export default function PermissionsPage() {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
  const [rows, setRows] = useState<Permission[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await client.get<Permission[]>("/roles/permissions");
      setRows(response.data);
    } catch {
      setError(t("permissions.errors.load"));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const toggle = async (permission: Permission) => {
    setBusy(permission.id);
    setError("");
    try {
      await client.put(`/roles/permissions/${permission.id}`, {
        is_active: !permission.is_active,
      });
      await load();
    } catch {
      setError(t("permissions.errors.update"));
    } finally {
      setBusy(null);
    }
  };

  return (
    <section className="space-y-6 p-6" dir={direction}>
      <header>
        <h1 className="text-2xl font-bold">{t("permissions.title")}</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          {t("permissions.description")}
        </p>
      </header>

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="font-semibold">{t("permissions.catalog")}</h2>
          <button
            className="rounded-lg border px-3 py-1.5 text-sm"
            onClick={() => void load()}
          >
            {t("common.refresh")}
          </button>
        </div>

        {loading ? (
          <div className="p-8 text-center">{t("common.loading")}</div>
        ) : (
          <div className="overflow-auto">
            <table className="w-full min-w-[760px] text-sm">
              <thead>
                <tr className="border-b bg-muted/40 text-start">
                  <th className="p-3 text-start">{t("permissions.name")}</th>
                  <th className="p-3 text-start">{t("permissions.resource")}</th>
                  <th className="p-3 text-start">{t("permissions.action")}</th>
                  <th className="p-3 text-start">{t("permissions.descriptionColumn")}</th>
                  <th className="p-3 text-start">{t("permissions.status")}</th>
                  <th className="p-3 text-start">{t("permissions.actions")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((permission) => (
                  <tr key={permission.id} className="border-b last:border-0">
                    <td className="p-3 font-medium">{permission.name}</td>
                    <td className="p-3">{permission.resource}</td>
                    <td className="p-3">{permission.action}</td>
                    <td className="p-3">{permission.description || "—"}</td>
                    <td className="p-3">
                      {permission.is_active
                        ? t("permissions.active")
                        : t("permissions.inactive")}
                    </td>
                    <td className="p-3">
                      <button
                        disabled={busy === permission.id}
                        onClick={() => void toggle(permission)}
                        className="rounded-lg border px-3 py-1.5 text-xs"
                      >
                        {busy === permission.id
                          ? t("common.processing")
                          : permission.is_active
                            ? t("permissions.deactivate")
                            : t("permissions.activate")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {!rows.length && (
              <div className="p-8 text-center text-muted-foreground">
                {t("permissions.empty")}
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
