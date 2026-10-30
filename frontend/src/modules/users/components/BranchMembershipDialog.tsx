import { useCallback, useEffect, useState } from "react";
import { GitBranch, Loader2 } from "lucide-react";
import { toast } from "react-hot-toast";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import apiClient from "@/shared/api/client";
import { getApiErrorMessage } from "@/shared/api/errors";
import type { User } from "../types/user";

interface Branch { id: number; company_id: number; name: string; code: string | null; is_active: boolean; }
interface BranchMember { user_id: number; username: string; full_name: string | null; is_active: boolean; }
interface Props { open: boolean; user: User | null; onOpenChange: (open: boolean) => void; }

export default function BranchMembershipDialog({ open, user, onOpenChange }: Props) {
  const [branches, setBranches] = useState<Branch[]>([]);
  const [assigned, setAssigned] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [loadError, setLoadError] = useState("");

  const load = useCallback(async () => {
    if (!user) return;
    setLoading(true);
    setLoadError("");
    try {
      const response = await apiClient.get<Branch[]>("/branches", { params: { active_only: true } });
      const activeBranches = response.data.filter((item) => item.is_active);
      const memberships = await Promise.all(activeBranches.map(async (item) => {
        const members = await apiClient.get<BranchMember[]>(`/branches/${item.id}/members`);
        return { id: item.id, assigned: members.data.some((member) => member.user_id === user.id && member.is_active) };
      }));
      setBranches(activeBranches);
      setAssigned(memberships.filter((item) => item.assigned).map((item) => item.id));
    } catch (error) {
      setBranches([]);
      setAssigned([]);
      setLoadError(getApiErrorMessage(error as never));
    } finally { setLoading(false); }
  }, [user]);

  useEffect(() => { if (open && user) void load(); }, [open, user, load]);

  const toggle = async (branch: Branch, checked: boolean) => {
    if (!user || savingId !== null) return;
    setSavingId(branch.id);
    try {
      if (checked) {
        await apiClient.post(`/branches/${branch.id}/members`, { user_id: user.id });
        setAssigned((current) => current.includes(branch.id) ? current : [...current, branch.id]);
        toast.success(`تم إسناد المستخدم إلى فرع ${branch.name}.`);
      } else {
        await apiClient.delete(`/branches/${branch.id}/members/${user.id}`);
        setAssigned((current) => current.filter((id) => id !== branch.id));
        toast.success(`تم إلغاء إسناد المستخدم من فرع ${branch.name}.`);
      }
    } catch (error) { toast.error(getApiErrorMessage(error as never)); }
    finally { setSavingId(null); }
  };

  return <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-xl" dir="rtl">
      <DialogHeader className="text-right">
        <DialogTitle className="flex items-center gap-2"><GitBranch className="h-5 w-5" />إدارة فروع المستخدم</DialogTitle>
        <DialogDescription>المستخدم: {user?.full_name || user?.username || ""}<span className="mt-1 block">حدد الفروع التي يمكن لهذا المستخدم الوصول إليها داخل الشركة.</span></DialogDescription>
      </DialogHeader>
      {loading ? <div className="flex min-h-36 items-center justify-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" />جاري تحميل الفروع والتعيينات...</div>
      : loadError ? <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">تعذر تحميل الفروع أو التعيينات. تحقق من صلاحية الوصول إلى الفروع وإدارتها.<p className="mt-2">{loadError}</p><Button className="mt-3" size="sm" variant="outline" onClick={() => void load()}>إعادة المحاولة</Button></div>
      : branches.length === 0 ? <div className="rounded-xl border p-5 text-center text-sm text-muted-foreground">لا توجد فروع نشطة متاحة لحسابك.</div>
      : <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-muted-foreground"><span>الفروع المتاحة</span><span>{assigned.length} من {branches.length} مُسندة</span></div>
        {branches.map((item) => <label key={item.id} className="flex cursor-pointer items-center justify-between gap-3 rounded-xl border p-3 transition-colors hover:bg-muted/50">
          <span className="min-w-0"><span className="block font-medium">{item.name}</span><span className="mt-1 block text-xs text-muted-foreground">{item.code ? `كود الفرع: ${item.code} · ` : ""}الشركة رقم {item.company_id}</span></span>
          <span className="flex shrink-0 items-center gap-2">{savingId === item.id && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
            <input type="checkbox" checked={assigned.includes(item.id)} disabled={savingId !== null || !user?.is_active} onChange={(event) => void toggle(item, event.target.checked)} className="h-4 w-4 accent-primary" aria-label={`تعيين ${user?.username} إلى ${item.name}`} />
          </span>
        </label>)}
        {!user?.is_active && <p className="text-xs text-amber-700">لا يمكن إسناد مستخدم غير نشط إلى فروع.</p>}
      </div>}
      <DialogFooter><Button type="button" variant="outline" onClick={() => onOpenChange(false)}>إغلاق</Button></DialogFooter>
    </DialogContent>
  </Dialog>;
}
