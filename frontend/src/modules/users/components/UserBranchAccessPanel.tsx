import { useCallback, useEffect, useState } from "react";
import { Loader2, ShieldCheck, UserRoundX } from "lucide-react";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import type { User } from "../types/user";
import {
  userCompanyAccessApi,
  type AccessibleBranch,
  type AssignableCompanyRole,
  type BranchMember,
} from "../api/user-company-access.api";

interface UserBranchAccessPanelProps {
  companyId: number;
  user: User;
  enabled: boolean;
}

export default function UserBranchAccessPanel({
  companyId,
  user,
  enabled,
}: UserBranchAccessPanelProps) {
  const { t } = useTranslation();
  const [branches, setBranches] = useState<AccessibleBranch[]>([]);
  const [branchId, setBranchId] = useState("");
  const [member, setMember] = useState<BranchMember | null>(null);
  const [roles, setRoles] = useState<AssignableCompanyRole[]>([]);
  const [roleId, setRoleId] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const loadBranches = useCallback(async () => {
    if (!enabled) {
      setBranches([]);
      setBranchId("");
      setMember(null);
      setRoles([]);
      setRoleId("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await userCompanyAccessApi.getBranches(companyId);
      setBranches(result);
      setBranchId((current) =>
        result.some((branch) => String(branch.id) === current)
          ? current
          : result.length === 1 ? String(result[0].id) : "",
      );
    } catch (requestError: any) {
      setBranches([]);
      setBranchId("");
      setError(requestError?.response?.data?.detail || t("users.companyAccess.loadBranchesFailed"));
    } finally {
      setLoading(false);
    }
  }, [companyId, enabled, t]);

  useEffect(() => {
    void loadBranches();
  }, [loadBranches]);

  const loadDetails = useCallback(async () => {
    if (!branchId || !enabled) {
      setMember(null);
      setRoles([]);
      setRoleId("");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const [members, assignableRoles] = await Promise.all([
        userCompanyAccessApi.getBranchMembers(companyId, Number(branchId)),
        userCompanyAccessApi.getAssignableBranchRoles(companyId, Number(branchId)),
      ]);
      const current = members.find((item) => item.user_id === user.id) ?? null;
      setMember(current);
      setRoles(assignableRoles);
      setRoleId(current?.role_id && assignableRoles.some((role) => role.id === current.role_id) ? String(current.role_id) : "");
    } catch (requestError: any) {
      setMember(null);
      setRoles([]);
      setRoleId("");
      setError(requestError?.response?.data?.detail || t("users.companyAccess.loadBranchDetailsFailed"));
    } finally {
      setLoading(false);
    }
  }, [branchId, companyId, enabled, user.id, t]);

  useEffect(() => {
    void loadDetails();
  }, [loadDetails]);

  async function grant() {
    if (!branchId || !user.is_active) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.grantBranch(companyId, Number(branchId), user.id, roleId ? Number(roleId) : null);
      toast.success(t("users.companyAccess.branchGranted"));
      await loadDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.branchSaveFailed"));
    } finally {
      setSaving(false);
    }
  }

  async function revoke() {
    if (!branchId || !member?.membership_is_active) return;
    const branchName = branches.find((branch) => String(branch.id) === branchId)?.name || branchId;
    if (!window.confirm(t("users.companyAccess.confirmBranchRevoke", { branch: branchName }))) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.revokeBranch(companyId, Number(branchId), user.id);
      toast.success(t("users.companyAccess.branchRevoked"));
      await loadDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.branchRevokeFailed"));
    } finally {
      setSaving(false);
    }
  }

  async function clearRole() {
    if (!branchId || !member?.membership_is_active || !member.role_id) return;
    setSaving(true);
    setError("");
    try {
      await userCompanyAccessApi.clearBranchRole(companyId, Number(branchId), user.id);
      toast.success(t("users.companyAccess.branchRoleCleared"));
      await loadDetails();
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || t("users.companyAccess.branchSaveFailed"));
    } finally {
      setSaving(false);
    }
  }

  const active = Boolean(member?.membership_is_active);

  return (
    <section className="space-y-4 rounded-xl border p-4">
      <div>
        <h3 className="font-semibold">{t("users.companyAccess.branchAccessTitle")}</h3>
        <p className="mt-1 text-xs text-muted-foreground">{t("users.companyAccess.branchAccessDescription")}</p>
      </div>
      <div className="space-y-2">
        <Label>{t("users.companyAccess.branch")}</Label>
        <Select value={branchId} onValueChange={setBranchId}>
          <SelectTrigger><SelectValue placeholder={t("users.companyAccess.selectBranch")} /></SelectTrigger>
          <SelectContent>
            {branches.map((branch) => (
              <SelectItem key={branch.id} value={String(branch.id)}>
                {branch.name}{branch.code ? ` · ${branch.code}` : ""}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {loading && <p className="text-xs text-muted-foreground">{t("users.companyAccess.loadingBranches")}</p>}
        {!loading && branches.length === 0 && !error && <p className="text-xs text-muted-foreground">{t("users.companyAccess.noBranches")}</p>}
      </div>
      {branchId && (
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm">
            {active ? <ShieldCheck className="h-4 w-4 text-emerald-600" /> : <UserRoundX className="h-4 w-4 text-muted-foreground" />}
            <span>{active ? t("users.companyAccess.branchMembershipActive") : t("users.companyAccess.branchMembershipMissing")}</span>
          </div>
          <div className="space-y-2">
            <Label>{t("users.companyAccess.branchRole")}</Label>
            <Select value={roleId} onValueChange={setRoleId}>
              <SelectTrigger><SelectValue placeholder={t("users.companyAccess.selectRole")} /></SelectTrigger>
              <SelectContent>
                {roles.map((role) => <SelectItem key={role.id} value={String(role.id)}>{role.name}</SelectItem>)}
              </SelectContent>
            </Select>
            {roles.length === 0 && <p className="text-xs text-muted-foreground">{t("users.companyAccess.noAssignableRoles")}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button type="button" size="sm" onClick={() => void grant()} disabled={saving || loading || !user.is_active}>
              {saving && <Loader2 className="me-2 h-4 w-4 animate-spin" />}
              {active ? t("users.companyAccess.saveChanges") : t("users.companyAccess.grantBranchAccess")}
            </Button>
            {active && (
              <>
                {member?.role_id && <Button type="button" size="sm" variant="outline" onClick={() => void clearRole()} disabled={saving}>{t("users.companyAccess.clearRole")}</Button>}
                <Button type="button" size="sm" variant="destructive" onClick={() => void revoke()} disabled={saving}>{t("users.companyAccess.revokeBranchAccess")}</Button>
              </>
            )}
          </div>
        </div>
      )}
      {error && <p className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
    </section>
  );
}
