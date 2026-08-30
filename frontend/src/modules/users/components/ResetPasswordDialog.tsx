import {
  Eye,
  EyeOff,
  Loader2,
} from "lucide-react";
import {
  type FormEvent,
  useEffect,
  useState,
} from "react";
import { toast } from "react-hot-toast";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

import { usersService } from "../services/users.service";
import type { User } from "../types/user";

interface ResetPasswordDialogProps {
  open: boolean;
  user: User | null;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => Promise<void>;
}

export default function ResetPasswordDialog({
  open,
  user,
  onOpenChange,
  onSuccess,
}: ResetPasswordDialogProps) {
  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [showPassword, setShowPassword] =
    useState(false);

  const [mustChangePassword, setMustChangePassword] =
    useState(true);

  const [loading, setLoading] =
    useState(false);

  useEffect(() => {
    if (open) {
      setPassword("");
      setConfirmPassword("");
      setMustChangePassword(true);
      setShowPassword(false);
    }
  }, [open]);

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!user) {
      return;
    }

    if (password.length < 6) {
      toast.error(
        "كلمة المرور يجب ألا تقل عن 6 أحرف.",
      );
      return;
    }

    if (password !== confirmPassword) {
      toast.error(
        "كلمتا المرور غير متطابقتين.",
      );
      return;
    }

    try {
      setLoading(true);

      await usersService.resetPassword(
        user.id,
        {
          new_password: password,
          must_change_password:
            mustChangePassword,
        },
      );

      toast.success(
        "تمت إعادة تعيين كلمة المرور.",
      );

      await onSuccess();

      onOpenChange(false);
    } catch (error) {
      console.error(
        "Reset password error:",
        error,
      );

      toast.error(
        "تعذر إعادة تعيين كلمة المرور.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent
        className="sm:max-w-md"
        dir="rtl"
      >
        <DialogHeader className="text-right">
          <DialogTitle>
            إعادة تعيين كلمة المرور
          </DialogTitle>

          <DialogDescription>
            المستخدم:{" "}
            {user?.full_name ||
              user?.username}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit}
          className="space-y-5"
        >
          <div className="space-y-2">
            <Label htmlFor="new_password">
              كلمة المرور الجديدة
            </Label>

            <div className="relative">
              <Input
                id="new_password"
                type={
                  showPassword
                    ? "text"
                    : "password"
                }
                value={password}
                onChange={(event) =>
                  setPassword(
                    event.target.value,
                  )
                }
                className="pl-11"
                required
              />

              <button
                type="button"
                onClick={() =>
                  setShowPassword(
                    (current) => !current,
                  )
                }
                className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confirm_password">
              تأكيد كلمة المرور
            </Label>

            <Input
              id="confirm_password"
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(
                  event.target.value,
                )
              }
              required
            />
          </div>

          <div className="flex items-center justify-between rounded-xl border p-4">
            <Label htmlFor="must-change">
              إجبار المستخدم على تغييرها
            </Label>

            <Switch
              id="must-change"
              checked={mustChangePassword}
              onCheckedChange={
                setMustChangePassword
              }
            />
          </div>

          <DialogFooter className="gap-2 sm:justify-start">
            <Button
              type="submit"
              disabled={loading}
            >
              {loading && (
                <Loader2 className="ml-2 h-4 w-4 animate-spin" />
              )}

              حفظ كلمة المرور
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() =>
                onOpenChange(false)
              }
            >
              إلغاء
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}