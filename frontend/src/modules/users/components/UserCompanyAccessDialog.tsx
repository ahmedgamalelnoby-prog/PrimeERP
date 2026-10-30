import { useEffect, useMemo, useState } from "react";
import { Building2, Loader2, Star } from "lucide-react";
import { toast } from "react-hot-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { usersApi, type UserCompany } from "../api/users.api";
import type { User } from "../types/user";
import { useAuth } from "@/modules/identity/context/AuthContext";

interface Props {
  user: User | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved?: () => void;
}

export default function UserCompanyAccessDialog({ user, open, onOpenChange, onSaved }: Props) {
  const [companies, setCompanies] = useState<UserCompany[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [defaultId, setDefaultId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { user: currentUser } = useAuth();

  useEffect(() => {
    if (!open || !user) return;
    let cancelled = false;
    const load = async () => {
      setLoading(true);
      try {
        const [availableResponse, accessResponse] = await Promise.all([
          usersApi.getAvailableCompanies(user.id),
          usersApi.getCompanyAccess(user.id),
        ]);
        if (cancelled) return;
        const available = availableResponse.data;
        const allowed = accessResponse.data.company_ids.filter((id) =>
          available.some((company) => company.id === id),
        );
        const initialDefault = accessResponse.data.default_company_id;
        setCompanies(available);
        setSelectedIds(allowed);
        setDefaultId(initialDefault && allowed.includes(initialDefault) ? initialDefault : (allowed[0] ?? null));
      } catch {
        if (!cancelled) toast.error("تعذر تحميل شركات المستخدم.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void load();
    return () => { cancelled = true; };
  }, [open, user]);

  const selectedCompanies = useMemo(
    () => companies.filter((company) => selectedIds.includes(company.id)),
    [companies, selectedIds],
  );

  const toggleCompany = (companyId: number, checked: boolean) => {
    const next = checked
      ? [...selectedIds, companyId]
      : selectedIds.filter((id) => id !== companyId);
    setSelectedIds(next);
    if (checked && defaultId === null) setDefaultId(companyId);
    if (!checked && defaultId === companyId) setDefaultId(next[0] ?? null);
  };

  const save = async () => {
    if (!user || selectedIds.length === 0 || defaultId === null || !selectedIds.includes(defaultId)) {
      toast.error("اختر شركة واحدة على الأقل وحدد الشركة الافتراضية.");
      return;
    }
    setSaving(true);
    try {
      await usersApi.updateCompanyAccess(user.id, {
        company_ids: selectedIds,
        default_company_id: defaultId,
      });
      if (currentUser?.id === user.id) {
        const currentCompanyId = Number(localStorage.getItem("company_id")) || 0;
        const nextCompanyId = selectedIds.includes(currentCompanyId) ? currentCompanyId : defaultId;
        localStorage.setItem("company_id", String(nextCompanyId));
      }
      toast.success("تم تحديث شركات المستخدم بنجاح.");
      onSaved?.();
      onOpenChange(false);
    } catch {
      toast.error("تعذر حفظ تعيين الشركات. راجع صلاحياتك وحاول مرة أخرى.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!saving) onOpenChange(next); }}>
      <DialogContent dir="rtl" className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader className="text-right">
          <DialogTitle className="flex items-center gap-2">
            <Building2 className="h-5 w-5" />
            شركات المستخدم
          </DialogTitle>
          <DialogDescription>
            {user ? `حدد الشركات المسموح لـ ${user.full_name || user.username} بالعمل عليها، ثم اختر الشركة الافتراضية.` : ""}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex min-h-40 items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" /> جاري تحميل الشركات...
          </div>
        ) : companies.length === 0 ? (
          <div className="rounded-lg border p-6 text-center text-sm text-muted-foreground">
            لا توجد شركات نشطة متاحة لهذا المستخدم.
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>الشركات المتاحة: {companies.length}</span>
              <span>تم اختيار: {selectedIds.length}</span>
            </div>
            <div className="max-h-80 space-y-2 overflow-y-auto rounded-lg border p-3">
              {companies.map((company) => {
                const checked = selectedIds.includes(company.id);
                const isDefault = defaultId === company.id;
                return (
                  <div key={company.id} className="flex items-center gap-3 rounded-md border-b p-3 last:border-0">
                    <input
                      id={`user-company-${company.id}`}
                      type="checkbox"
                      checked={checked}
                      onChange={(event) => toggleCompany(company.id, event.target.checked)}
                      className="h-4 w-4 accent-primary"
                    />
                    <label htmlFor={`user-company-${company.id}`} className="min-w-0 flex-1 cursor-pointer">
                      <span className="block font-medium">{company.name}</span>
                      {company.code && <span className="text-xs text-muted-foreground">كود: {company.code}</span>}
                    </label>
                    <Button
                      type="button"
                      size="sm"
                      variant={isDefault ? "default" : "outline"}
                      disabled={!checked}
                      onClick={() => setDefaultId(company.id)}
                      className="shrink-0"
                    >
                      <Star className="ml-1 h-3.5 w-3.5" />
                      {isDefault ? "افتراضية" : "تعيين افتراضية"}
                    </Button>
                  </div>
                );
              })}
            </div>
            <p className="text-xs text-muted-foreground">
              الشركة الافتراضية هي التي يتم فتح النظام عليها عند تسجيل الدخول لأول مرة أو عند عدم وجود اختيار سابق صالح.
            </p>
          </div>
        )}

        <DialogFooter className="gap-2 sm:justify-start">
          <Button type="button" onClick={() => void save()} disabled={loading || saving || companies.length === 0 || selectedCompanies.length === 0}>
            {saving && <Loader2 className="ml-2 h-4 w-4 animate-spin" />}
            حفظ التعيين
          </Button>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)} disabled={saving}>
            إلغاء
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
