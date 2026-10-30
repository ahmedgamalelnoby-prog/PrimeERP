import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Info, Loader2, RefreshCw, ShieldCheck } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import { rolesApi } from "../api/roles.api";
import type { RoleAccessAudit } from "../types/access-audit";

interface RoleAccessAuditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function RoleAccessAuditDialog({ open, onOpenChange }: RoleAccessAuditDialogProps) {
  const { t, i18n } = useTranslation();
  const [audit, setAudit] = useState<RoleAccessAudit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loadAudit = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setAudit(await rolesApi.accessAudit());
    } catch (requestError: any) {
      setAudit(null);
      setError(requestError?.response?.data?.detail || t("roles.accessAudit.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    if (open) void loadAudit();
  }, [open, loadAudit]);

  const direction = i18n.dir();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-6xl" dir={direction}>
        <DialogHeader className="text-start">
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5" />
            {t("roles.accessAudit.title")}
          </DialogTitle>
          <DialogDescription>{t("roles.accessAudit.description")}</DialogDescription>
        </DialogHeader>

        <div className="flex justify-end">
          <Button type="button" variant="outline" size="sm" onClick={() => void loadAudit()} disabled={loading}>
            <RefreshCw className="me-2 h-4 w-4" />{t("common.refresh")}
          </Button>
        </div>

        {error && <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}

        {loading ? (
          <div className="flex min-h-48 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>
        ) : audit ? (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                [t("roles.accessAudit.roles"), audit.summary.roles_total],
                [t("roles.accessAudit.activeRoles"), audit.summary.roles_active],
                [t("roles.accessAudit.permissions"), audit.summary.permissions_total],
                [t("roles.accessAudit.findings"), audit.summary.findings_total],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-xl border p-4">
                  <p className="text-sm text-muted-foreground">{label}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
                </div>
              ))}
            </section>

            <section className="space-y-3">
              <h3 className="font-semibold">{t("roles.accessAudit.roleCoverage")}</h3>
              <div className="overflow-x-auto rounded-lg border">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t("roles.accessAudit.role")}</TableHead>
                      <TableHead>{t("roles.accessAudit.status")}</TableHead>
                      <TableHead>{t("roles.accessAudit.permissions")}</TableHead>
                      <TableHead>{t("roles.accessAudit.globalUsersActive")}</TableHead>
                      <TableHead>{t("roles.accessAudit.companyGrantsActive")}</TableHead>
                      <TableHead>{t("roles.accessAudit.companyGrantsInactive")}</TableHead>
                      <TableHead>{t("roles.accessAudit.branchGrantsActive")}</TableHead>
                      <TableHead>{t("roles.accessAudit.branchGrantsInactive")}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {audit.roles.map((role) => (
                      <TableRow key={role.id}>
                        <TableCell>
                          <div className="font-medium">{role.name}</div>
                          {role.description && <div className="text-xs text-muted-foreground">{role.description}</div>}
                        </TableCell>
                        <TableCell>
                          {role.is_active
                            ? <span className="text-emerald-700">{t("roles.accessAudit.active")}</span>
                            : <span className="text-amber-700">{t("roles.accessAudit.inactive")}</span>}
                        </TableCell>
                        <TableCell>
                          <span className="font-medium tabular-nums">{role.active_permission_count}</span>
                          <span className="text-muted-foreground"> / {role.permission_count}</span>
                          {role.inactive_permission_count > 0 && <div className="text-xs text-amber-700">{t("roles.accessAudit.inactivePermissions", { count: role.inactive_permission_count })}</div>}
                        </TableCell>
                        <TableCell className="tabular-nums">{role.usage.global_users_active}<span className="text-muted-foreground"> / {role.usage.global_users_inactive}</span></TableCell>
                        <TableCell className="tabular-nums">{role.usage.company_memberships_active}</TableCell>
                        <TableCell className="tabular-nums">{role.usage.company_memberships_inactive}</TableCell>
                        <TableCell className="tabular-nums">{role.usage.branch_memberships_active}</TableCell>
                        <TableCell className="tabular-nums">{role.usage.branch_memberships_inactive}</TableCell>
                      </TableRow>
                    ))}
                    {audit.roles.length === 0 && <TableRow><TableCell colSpan={8} className="py-8 text-center text-muted-foreground">{t("roles.accessAudit.noRoles")}</TableCell></TableRow>}
                  </TableBody>
                </Table>
              </div>
            </section>

            <section className="space-y-3">
              <h3 className="font-semibold">{t("roles.accessAudit.findings")}</h3>
              {audit.findings.length === 0 ? (
                <div className="flex items-center gap-2 rounded-lg border p-4 text-sm text-emerald-700">
                  <CheckCircle2 className="h-5 w-5" />{t("roles.accessAudit.noFindings")}
                </div>
              ) : (
                <div className="space-y-2">
                  {audit.findings.map((finding, index) => (
                    <div key={`${finding.code}-${finding.role_id ?? finding.permission_id ?? index}`} className="flex items-start gap-3 rounded-lg border p-3">
                      {finding.severity === "warning"
                        ? <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
                        : <Info className="mt-0.5 h-4 w-4 shrink-0 text-blue-600" />}
                      <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium">
                          {t(`roles.accessAudit.findingTypes.${finding.code}`, {
                            role: finding.role_name,
                            permission: finding.permission_name,
                            count: finding.count,
                            defaultValue: finding.code,
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {audit.permissions_without_active_role.length > 0 && (
              <section className="space-y-3">
                <h3 className="font-semibold">{t("roles.accessAudit.unassignedPermissions")}</h3>
                <div className="flex flex-wrap gap-2">
                  {audit.permissions_without_active_role.map((permission) => (
                    <span key={permission.id} className="rounded-full border px-3 py-1 text-xs">
                      {permission.name}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>{t("common.close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
