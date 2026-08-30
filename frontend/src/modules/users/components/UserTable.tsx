import {
  KeyRound,
  Loader2,
  Pencil,
  ShieldCheck,
  Trash2,
  UserCircle,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

import type { User } from "../types/user";
import UserStatus from "./UserStatus";

interface UserTableProps {
  users: User[];
  loading: boolean;
  processingId: number | null;

  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onToggleStatus: (user: User) => void;
  onResetPassword: (user: User) => void;
}

function getUserDisplayName(user: User): string {
  return user.full_name?.trim() || user.username;
}

function getUserInitial(user: User): string {
  const displayName = getUserDisplayName(user);

  return displayName.charAt(0).toUpperCase();
}

function formatLastLogin(value: string | null): string {
  if (!value) {
    return "لم يسجل الدخول";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "غير متاح";
  }

  return new Intl.DateTimeFormat("ar-EG", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export default function UserTable({
  users,
  loading,
  processingId,
  onEdit,
  onDelete,
  onToggleStatus,
  onResetPassword,
}: UserTableProps) {
  if (loading) {
    return (
      <div
        className="flex min-h-80 items-center justify-center rounded-2xl border bg-card"
        dir="rtl"
      >
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />

          <p className="mt-3 text-sm text-muted-foreground">
            جاري تحميل المستخدمين...
          </p>
        </div>
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div
        className="flex min-h-80 flex-col items-center justify-center rounded-2xl border bg-card p-8 text-center"
        dir="rtl"
      >
        <UserCircle className="h-12 w-12 text-muted-foreground" />

        <h3 className="mt-4 text-lg font-semibold">
          لا يوجد مستخدمون
        </h3>

        <p className="mt-2 text-sm text-muted-foreground">
          لا توجد نتائج مطابقة للبحث أو عوامل التصفية الحالية.
        </p>
      </div>
    );
  }

  return (
    <div
      className="overflow-hidden rounded-2xl border bg-card shadow-sm"
      dir="rtl"
    >
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="min-w-52 text-right">
                المستخدم
              </TableHead>

              <TableHead className="min-w-56 text-right">
                البريد الإلكتروني
              </TableHead>

              <TableHead className="min-w-32 text-right">
                الدور
              </TableHead>

              <TableHead className="min-w-28 text-right">
                الحالة
              </TableHead>

              <TableHead className="min-w-40 text-right">
                آخر تسجيل دخول
              </TableHead>

              <TableHead className="min-w-28 text-right">
                تفعيل الحساب
              </TableHead>

              <TableHead className="min-w-40 text-center">
                الإجراءات
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {users.map((user) => {
              const processing =
                processingId === user.id;

              const displayName =
                getUserDisplayName(user);

              return (
                <TableRow key={user.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 font-semibold text-primary">
                        {getUserInitial(user)}
                      </div>

                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <p className="truncate font-medium">
                            {displayName}
                          </p>

                          {user.is_superuser && (
                            <ShieldCheck
                              className="h-4 w-4 shrink-0 text-amber-600"
                              aria-label="مستخدم بصلاحيات مدير"
                            />
                          )}

                          {user.is_platform_admin && (
                            <span className="rounded-full bg-purple-500/10 px-2 py-0.5 text-xs font-medium text-purple-700">
                              مدير المنصة
                            </span>
                          )}
                        </div>

                        <p className="mt-1 truncate text-xs text-muted-foreground">
                          @{user.username}
                        </p>
                      </div>
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="min-w-0">
                      <p className="truncate text-sm">
                        {user.email}
                      </p>

                      {user.phone && (
                        <p className="mt-1 truncate text-xs text-muted-foreground">
                          {user.phone}
                        </p>
                      )}
                    </div>
                  </TableCell>

                  <TableCell>
                    <span className="text-sm">
                      {user.role_name || "بدون دور"}
                    </span>
                  </TableCell>

                  <TableCell>
                    <UserStatus
                      isActive={user.is_active}
                    />
                  </TableCell>

                  <TableCell>
                    <span className="whitespace-nowrap text-sm text-muted-foreground">
                      {formatLastLogin(
                        user.last_login,
                      )}
                    </span>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={user.is_active}
                        disabled={processing}
                        onCheckedChange={() =>
                          onToggleStatus(user)
                        }
                        aria-label={
                          user.is_active
                            ? "تعطيل المستخدم"
                            : "تفعيل المستخدم"
                        }
                      />

                      {processing && (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      )}
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center justify-center gap-1">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        disabled={processing}
                        onClick={() =>
                          onEdit(user)
                        }
                        title="تعديل المستخدم"
                        aria-label="تعديل المستخدم"
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        disabled={processing}
                        onClick={() =>
                          onResetPassword(user)
                        }
                        title="إعادة تعيين كلمة المرور"
                        aria-label="إعادة تعيين كلمة المرور"
                      >
                        <KeyRound className="h-4 w-4" />
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        disabled={processing}
                        onClick={() =>
                          onDelete(user)
                        }
                        title="حذف المستخدم"
                        aria-label="حذف المستخدم"
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      >
                        {processing ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4" />
                        )}
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}