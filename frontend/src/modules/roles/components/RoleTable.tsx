import {
  Loader2,
  Pencil,
  ShieldCheck,
  Trash2,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
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

import type { Role } from "../types/role";
import RoleStatus from "./RoleStatus";

interface RoleTableProps {
  roles: Role[];
  loading: boolean;
  processingId: number | null;

  onEdit: (role: Role) => void;
  onDelete: (role: Role) => void;
  onToggleStatus: (role: Role) => void;
}

export default function RoleTable({
  roles,
  loading,
  processingId,
  onEdit,
  onDelete,
  onToggleStatus,
}: RoleTableProps) {
  if (loading) {
    return (
      <div className="flex min-h-80 items-center justify-center rounded-2xl border bg-card">
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />

          <p className="mt-3 text-sm text-muted-foreground">
            جاري تحميل الأدوار...
          </p>
        </div>
      </div>
    );
  }

  if (roles.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-2xl border bg-card p-8 text-center">
        <ShieldCheck className="h-12 w-12 text-muted-foreground" />

        <h3 className="mt-4 text-lg font-semibold">
          لا توجد أدوار
        </h3>

        <p className="mt-2 text-sm text-muted-foreground">
          ابدأ بإنشاء أول دور وتحديد صلاحياته.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border bg-card shadow-sm">
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-right">
                الدور
              </TableHead>

              <TableHead className="text-right">
                الصلاحيات
              </TableHead>

              <TableHead className="text-right">
                المستخدمون
              </TableHead>

              <TableHead className="text-right">
                الحالة
              </TableHead>

              <TableHead className="text-right">
                تفعيل الدور
              </TableHead>

              <TableHead className="text-center">
                الإجراءات
              </TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {roles.map((role) => {
              const processing =
                processingId === role.id;

              return (
                <TableRow key={role.id}>
                  <TableCell>
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary">
                        <ShieldCheck className="h-5 w-5" />
                      </div>

                      <div>
                        <p className="font-medium">
                          {role.name}
                        </p>

                        <p className="mt-1 max-w-xs truncate text-xs text-muted-foreground">
                          {role.description ||
                            "لا يوجد وصف"}
                        </p>
                      </div>
                    </div>
                  </TableCell>

                  <TableCell>
                    <Badge variant="outline">
                      {role.permissions.length} صلاحية
                    </Badge>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span>
                        {role.users_count}
                      </span>
                    </div>
                  </TableCell>

                  <TableCell>
                    <RoleStatus
                      isActive={role.is_active}
                    />
                  </TableCell>

                  <TableCell>
                    <Switch
                      checked={role.is_active}
                      disabled={processing}
                      onCheckedChange={() =>
                        onToggleStatus(role)
                      }
                    />
                  </TableCell>

                  <TableCell>
                    <div className="flex justify-center gap-1">
                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        title="تعديل الدور"
                        disabled={processing}
                        onClick={() =>
                          onEdit(role)
                        }
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>

                      <Button
                        type="button"
                        size="icon"
                        variant="ghost"
                        title="حذف الدور"
                        disabled={processing}
                        className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                        onClick={() =>
                          onDelete(role)
                        }
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