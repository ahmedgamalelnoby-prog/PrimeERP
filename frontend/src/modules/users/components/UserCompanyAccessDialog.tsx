import { useEffect, useState } from "react";
import { Building2, Loader2 } from "lucide-react";
import toast from "react-hot-toast";

import { Button } from "@/components/ui/button";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter,
  DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import client from "@/shared/api/client";
import type { User } from "../types/user";

interface CompanyAccessRow {
  id: number;
  name: string;
  code: string | null;
  is_active: boolean;
  has_access: boolean;
  is_default: boolean;
}

interface Props {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function UserCompanyAccessDialog({ user, open, onOpenChange }: Props) {
  const [rows, setRows] = useState<CompanyAccessRow[]>([]);
  const [originalRows, setOriginalRows] = useState<CompanyAccessRow[]>([]);
  const [defaultCompanyId, setDefaultCompanyId] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!open || !user) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    void client.get<CompanyAccessRow[]>(`/companies/users/${user.id}/access`)
      .then(({ data }) => {
        if (cancelled) return;
        setRows(data);
        setOriginalRows(data);
        const selected = data.find((row) => row.has_access && row.is_default && row.is_active)
          ?? data.find((row) => row.has_access && row.is_active);
        setDefaultCompanyId(selected ? String(selected.id) : "");
      })
      .catch((requestError: any) => {
        if (!cancelled) setError(requestError?.response?.data?.detail || "تعذر تحميل صلاحيات الشركات.");
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [open, user]);

  const toggleAccess = (id: number, checked: boolean) => {
    setRows((current) => current.map((row) => row.id === id ? { ...row, has_access: checked } : row));
    if (!checked && defaultCompanyId === String(id)) {
      const replacement = rows.find((row) => row.id !== id && row.has_access);
      setDefaultCompanyId(replacement ? String(replacement.id) : "");
    }
    if (checked && !defaultCompanyId) setDefaultCompanyId(String(id));
  };

  const save = async () => {
    if (!user) return;
    const selected = rows.filter((row) => row.has_access);
    if (selected.length && !selected.some((row) => String(row.id) === defaultCompanyId)) {
      setError("اختر شركة افتراضية من الشركات المصرح بها.");
      return;
    }
    setSaving(true);
    setError("");
    try {
      for (const original of originalRows) {
        const current = rows.find((row) => row.id === original.id);
        if (original.has_access && !current?.has_access) {
          await client.delete(`/companies/${original.id}/users/${user.id}/access`);
        }
      }
      for (const row of selected) {
        const original = originalRows.find((item) => item.id === row.id);
        const shouldBeDefault = String(row.id) === defaultCompanyId;
        if (!original?.has_access || (shouldBeDefault && !original.is_default)) {
          await client.put(`/companies/${row.id}/users/${user.id}/access`, null, {
            params: { is_default: shouldBeDefault },
          });
        }
      }
      toast.success("تم تحديث صلاحيات الشركات.");
      onOpenChange(false);
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || "تعذر حفظ صلاحيات الشركات.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(next) => !saving && onOpenChange(next)}>
      <DialogContent dir="rtl" className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader className="text-right">
          <DialogTitle className="flex items-center gap-2"><Building2 className="h-5 w-5 text-primary" />صلاحيات الشركات</DialogTitle>
          <DialogDescription>
            {user ? `حدد الشركات التي يستطيع ${user.full_name || user.username} الوصول إليها، واختر الشركة الافتراضية.` : ""}
          </DialogDescription>
        </DialogHeader>
        {loading ? (
          <div className="flex min-h-32 items-center justify-center"><Loader2 className="h-6 w-6 animate-spin" /></div>
        ) : (
          <div className="space-y-3">
            {rows.map((row) => (
              <div key={row.id} className="flex items-center justify-between gap-3 rounded-xl border p-3">
                <label className="flex min-w-0 items-center gap-3">
                  <input type="checkbox" checked={row.has_access} disabled={(!row.is_active && !row.has_access) || saving}
                    onChange={(event) => toggleAccess(row.id, event.target.checked)} />
                  <span className="min-w-0">
                    <span className="block truncate text-sm font-semibold">{row.name}</span>
                    <span className="block text-xs text-muted-foreground">{row.code || "بدون كود"}{!row.is_active ? " · غير نشطة" : ""}</span>
                  </span>
                </label>
                <label className="flex shrink-0 items-center gap-2 text-xs text-muted-foreground">
                  <input type="radio" name="default-company" value={row.id}
                    checked={defaultCompanyId === String(row.id)} disabled={!row.has_access || !row.is_active || saving}
                    onChange={() => setDefaultCompanyId(String(row.id))} />
                  افتراضية
                </label>
              </div>
            ))}
            {rows.length === 0 && <p className="py-6 text-center text-sm text-muted-foreground">لا توجد شركات في هذا الحساب.</p>}
          </div>
        )}
        {error && <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">{error}</p>}
        <DialogFooter>
          <Button type="button" variant="outline" disabled={saving} onClick={() => onOpenChange(false)}>إلغاء</Button>
          <Button type="button" disabled={loading || saving} onClick={() => void save()}>
            {saving ? <><Loader2 className="ml-2 h-4 w-4 animate-spin" />جارٍ الحفظ</> : "حفظ الصلاحيات"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
