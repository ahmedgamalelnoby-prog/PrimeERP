import { useCallback, useEffect, useMemo, useState } from "react";
import { Building2, Loader2, RefreshCw, ShieldCheck, ShieldX, UserRoundX } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

import {
  userCompanyAccessApi,
  type AccessibleCompany,
  type CompanyAccessAudit,
  type CompanyAccessAuditMember,
} from "../api/user-company-access.api";

interface UserAccessAuditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onManageUser: (userId: number) => void;
}

export default function UserAccessAuditDialog({ open, onOpenChange, onManageUser }: UserAccessAuditDialogProps) {
  const { t, i18n } = useTranslation();
  const [companies, setCompanies] = useState<AccessibleCompany[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [audit, setAudit] = useState<CompanyAccessAudit | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const direction = i18n.dir();

  const loadCompanies = useCallback(async () => {
    try {
      setError("");
      const result = await userCompanyAccessApi.getCompanies();
      setCompanies(result);
      setCompanyId((current) =>
        result.some((company) => String(company.id) === current)
          ? current
          : result.length ? String(result[0].id) : "",
      );
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.accessAudit.loadCompaniesFailed"));
    }
  }, [t]);

  const loadAudit = useCallback(async () => {
    if (!companyId) {
      setAudit(null);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await userCompanyAccessApi.getAccessAudit(Number(companyId), page, 50);
      setAudit(result);
    } catch (requestError: any) {
      setAudit(null);
      setError(requestError?.response?.data?.detail || t("users.accessAudit.loadFailed"));
    } finally {
      setLoading(false);
    }
  }, [companyId, page, t]);

  useEffect(() => {
    if (open) void loadCompanies();
  }, [open, loadCompanies]);

  useEffect(() => {
    if (open && companyId) void loadAudit();
  }, [open, companyId, page, loadAudit]);

  const visibleMembers = useMemo(() => {
    const query = search.trim().toLocaleLowerCase();
    if (!query) return audit?.items ?? [];
    return (audit?.items ?? []).filter((member) =>
      [member.username, member.full_name ?? ""].some((value) => value.toLocaleLowerCase().includes(query)),
    );
  }, [audit, search]);

  function membershipStatus(active: boolean | null) {
    if (active === null) {
      return <span className="text-muted-foreground">{t("users.accessAudit.noAccess")}</span>;
    }
    return active
      ? <span className="inline-flex items-center gap-1 text-emerald-700"><ShieldCheck className="h-4 w-4" />{t("users.accessAudit.active")}</span>
      : <span className="inline-flex items-center gap-1 text-amber-700"><ShieldX className="h-4 w-4" />{t("users.accessAudit.revoked")}</span>;
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[88vh] overflow-y-auto sm:max-w-6xl" dir={direction}>
        <DialogHeader className="text-start">
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {t("users.accessAudit.title")}
          </DialogTitle>
          <DialogDescription>{t("users.accessAudit.description")}</DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1 space-y-2">
            <label className="text-sm font-medium">{t("users.accessAudit.company")}</label>
            <Select value={companyId} onValueChange={(value) => { setCompanyId(value); setPage(1); }}>
              <SelectTrigger><SelectValue placeholder={t("users.accessAudit.selectCompany")} /></SelectTrigger>
              <SelectContent>
                {companies.map((company) => (
                  <SelectItem key={company.id} value={String(company.id)}>
                    {company.name}{company.code ? ` · ${company.code}` : ""}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="min-w-0 flex-1 space-y-2">
            <label className="text-sm font-medium">{t("users.accessAudit.search")}</label>
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={t("users.accessAudit.searchPlaceholder")} />
          </div>
          <Button type="button" variant="outline" onClick={() => void loadAudit()} disabled={loading || !companyId}>
            <RefreshCw className="me-2 h-4 w-4" />{t("common.refresh")}
          </Button>
        </div>

        {error && <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}

        {loading ? (
          <div className="flex min-h-40 items-center justify-center"><Loader2 className="h-7 w-7 animate-spin text-muted-foreground" /></div>
        ) : audit ? (
          <>
            <div className="flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground">
              <span>{audit.company_name}</span>
              <span>{t("users.accessAudit.memberCount", { count: audit.total })}</span>
            </div>
            <div className="overflow-x-auto rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="min-w-48">{t("users.accessAudit.user")}</TableHead>
                    <TableHead className="min-w-36">{t("users.accessAudit.companyAccess")}</TableHead>
                    <TableHead className="min-w-36">{t("users.accessAudit.companyRole")}</TableHead>
                    <TableHead className="min-w-28">{t("users.accessAudit.actions")}</TableHead>
                    {audit.branches.map((branch) => (
                      <TableHead key={branch.id} className="min-w-44">
                        <div>{branch.name}</div>
                        {!branch.is_active && <span className="text-xs text-amber-700">{t("users.accessAudit.branchInactive")}</span>}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {visibleMembers.map((member: CompanyAccessAuditMember) => (
                    <TableRow key={member.user_id}>
                      <TableCell>
                        <div className="font-medium">{member.full_name || member.username}</div>
                        <div className="text-xs text-muted-foreground">@{member.username}</div>
                        {!member.user_is_active && (
                          <div className="mt-1 inline-flex items-center gap-1 text-xs text-destructive">
                            <UserRoundX className="h-3 w-3" />{t("users.accessAudit.userDisabled")}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>{membershipStatus(member.company_membership_is_active)}</TableCell>
                      <TableCell>{member.company_role_name || t("users.accessAudit.noRole")}</TableCell>
                      <TableCell>
                        <Button type="button" size="sm" variant="outline" onClick={() => onManageUser(member.user_id)}>
                          {t("users.accessAudit.manage")}
                        </Button>
                      </TableCell>
                      {audit.branches.map((branch) => {
                        const grant = member.branch_access.find((item) => item.branch_id === branch.id);
                        return (
                          <TableCell key={branch.id}>
                            <div>{membershipStatus(grant?.membership_is_active ?? null)}</div>
                            {grant?.role_name && <div className="mt-1 text-xs text-muted-foreground">{grant.role_name}</div>}
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                  {visibleMembers.length === 0 && (
                    <TableRow><TableCell colSpan={4 + audit.branches.length} className="h-24 text-center text-muted-foreground">{t("users.accessAudit.noMembers")}</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </div>
            <div className="flex items-center justify-between gap-3">
              <span className="text-xs text-muted-foreground">{t("users.accessAudit.page", { page: audit.page, pages: Math.max(audit.total_pages, 1) })}</span>
              <div className="flex gap-2">
                <Button type="button" size="sm" variant="outline" disabled={page <= 1 || loading} onClick={() => setPage((value) => Math.max(1, value - 1))}>{t("users.accessAudit.previous")}</Button>
                <Button type="button" size="sm" variant="outline" disabled={page >= audit.total_pages || loading} onClick={() => setPage((value) => value + 1)}>{t("users.accessAudit.next")}</Button>
              </div>
            </div>
          </>
        ) : !error ? (
          <div className="py-12 text-center text-sm text-muted-foreground">{t("users.accessAudit.selectCompany")}</div>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>{t("common.close")}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
