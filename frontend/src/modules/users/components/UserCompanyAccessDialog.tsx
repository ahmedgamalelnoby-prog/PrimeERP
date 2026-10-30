import { Building2, Loader2, ShieldCheck, UserRoundX } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import type { User } from "../types/user";
import UserBranchAccessPanel from "./UserBranchAccessPanel";
import {
  userCompanyAccessApi,
  type AccessibleCompany,
  type AssignableCompanyRole,
  type CompanyMember,
} from "../api/user-company-access.api";

interface UserCompanyAccessDialogProps {
  open: boolean;
  user: User | null;
  onOpenChange: (open: boolean) => void;
}

export default function UserCompanyAccessDialog({
  open,
  user,
  onOpenChange,
}: UserCompanyAccessDialogProps) {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
  const [companies, setCompanies] = useState<AccessibleCompany[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [member, setMember] = useState<CompanyMember | null>(null);
  const [roles, setRoles] = useState<AssignableCompanyRole[]>([]);
  const [roleId, setRoleId] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const selectedCompany = useMemo(
    () => companies.find((company) => String(company.id) === companyId) ?? null,
    [companies, companyId],
  );

  const loadCompanies = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const result = await userCompanyAccessApi.getCompanies();
      setCompanies(result);
      setCompanyId((current) =>
        result.some((company) => String(company.id) === current)
          ? current
          : result.length === 1 ? String(result[0].id) : "",
      );
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.loadCompaniesFailed"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  const loadCompanyDetails = useCallback(async () => {
    if (!companyId || !user) {
      setMember(null);
      setRoles([]);
      setRoleId("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [members, assignableRoles] = await Promise.all([
        userCompanyAccessApi.getMembers(Number(companyId)),
        userCompanyAccessApi.getAssignableRoles(Number(companyId)),
      ]);
      const current = members.find((item) => item.user_id === user.id) ?? null;
      setMember(current);
      setRoles(assignableRoles);
      setRoleId(current?.role_id && assignableRoles.some((role) => role.id === current.role_id) ? String(current.role_id) : "");
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.loadDetailsFailed"));
      setMember(null);
      setRoles([]);
      setRoleId("");
    } finally {
      setLoading(false);
    }
  }, [companyId, user, t]);

  useEffect(() => {
    if (open) void loadCompanies();
  }, [open, loadCompanies]);

  useEffect(() => {
    if (open && companyId) void loadCompanyDetails();
  }, [open, companyId, loadCompanyDetails]);

  async function saveMembership() {
    if (!user || !selectedCompany) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.grant(
        selectedCompany.id,
        user.id,
        roleId ? Number(roleId) : null,
      );
      toast.success(t("users.companyAccess.granted"));
      await loadCompanyDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.saveFailed"));
    } finally {
      setSaving(false);
    }
  }

  async function revokeMembership() {
    if (!user || !selectedCompany || !member?.membership_is_active) return;
    if (!window.confirm(t("users.companyAccess.confirmRevoke", { company: selectedCompany.name }))) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.revoke(selectedCompany.id, user.id);
      toast.success(t("users.companyAccess.revoked"));
      await loadCompanyDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.revokeFailed"));
    } finally {
      setSaving(false);
    }
  }

  async function clearRole() {
    if (!user || !selectedCompany || !member?.membership_is_active || !member.role_id) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.clearRole(selectedCompany.id, user.id);
      toast.success(t("users.companyAccess.roleCleared"));
      await loadCompanyDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.saveFailed"));
    } finally {
      setSaving(false);
    }
  }

  const active = Boolean(member?.membership_is_active);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl" dir={direction}>
        <DialogHeader className="text-start">
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            {t("users.companyAccess.title")}
          </DialogTitle>
          <DialogDescription>
            {user?.full_name || user?.username} · @{user?.username}
          </DialogDescription>
        </DialogHeader>

        {loading && companies.length === 0 ? (
          <div className="flex min-h-32 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-5">
            <div className="space-y-2">
              <Label>{t("users.companyAccess.company")}</Label>
              <Select value={companyId} onValueChange={setCompanyId}>
                <SelectTrigger>
                  <SelectValue placeholder={t("users.companyAccess.selectCompany")} />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={String(company.id)}>
                      {company.name}{company.code ? ` · ${company.code}` : ""}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {companies.length === 0 && (
                <p className="text-sm text-muted-foreground">{t("users.companyAccess.noCompanies")}</p>
              )}
            </div>

            {selectedCompany && (
              <>
              <div className="rounded-xl border p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    {active ? <ShieldCheck className="h-5 w-5 text-emerald-600" /> : <UserRoundX className="h-5 w-5 text-muted-foreground" />}
                    <div>
                      <p className="font-medium">{active ? t("users.companyAccess.activeMembership") : t("users.companyAccess.noMembership")}</p>
                      <p className="text-xs text-muted-foreground">{selectedCompany.name}</p>
                    </div>
                  </div>
                  {(!user?.is_active || (member && !member.user_is_active)) && (
                    <span className="text-xs text-destructive">{t("users.companyAccess.userDisabled")}</span>
                  )}
                </div>

                <div className="mt-4 space-y-2">
                  <Label>{t("users.companyAccess.role")}</Label>
                  <Select value={roleId} onValueChange={setRoleId}>
                    <SelectTrigger>
                      <SelectValue placeholder={t("users.companyAccess.selectRole")} />
                    </SelectTrigger>
                    <SelectContent>
                      {roles.map((role) => (
                        <SelectItem key={role.id} value={String(role.id)}>
                          {role.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {roles.length === 0 && (
                    <p className="text-xs text-muted-foreground">{t("users.companyAccess.noAssignableRoles")}</p>
                  )}
                  <p className="text-xs text-muted-foreground">{t("users.companyAccess.roleSecurityHint")}</p>
                </div>

                {error && <p className="mt-3 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}

                <div className="mt-4 flex flex-wrap gap-2">
                  <Button type="button" onClick={() => void saveMembership()} disabled={saving || loading || !user?.is_active}>
                    {saving && <Loader2 className="me-2 h-4 w-4 animate-spin" />}
                    {active ? t("users.companyAccess.saveChanges") : t("users.companyAccess.grantAccess")}
                  </Button>
                  {active && (
                    <>
                      {member?.role_id && (
                        <Button type="button" variant="outline" onClick={() => void clearRole()} disabled={saving}>
                          {t("users.companyAccess.clearRole")}
                        </Button>
                      )}
                      <Button type="button" variant="destructive" onClick={() => void revokeMembership()} disabled={saving}>
                        {t("users.companyAccess.revokeAccess")}
                      </Button>
                    </>
                  )}
                </div>
              </div>
              {user && (
                <UserBranchAccessPanel
                  companyId={selectedCompany.id}
                  user={user}
                  enabled={true}
                  companyMembershipActive={active}
                />
              )}
              </>
            )}
            {error && !selectedCompany && <p className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            {t("common.close")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
