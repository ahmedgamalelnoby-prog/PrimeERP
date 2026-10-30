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
import { useTranslation } from "react-i18next";

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
} : RoleTableProps) {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
  if (loading) {
    return (
      <div className="flex min-h-80 items-center justify-center rounded-2xl border bg-card" dir={direction}>
        <div className="text-center">
          <Loader2 className="mx-auto h-8 w-8 animate-spin text-primary" />

          <p className="mt-3 text-sm text-muted-foreground">
            {t("rolesTable.loading")}
          </p>
        </div>
      </div>
    );
  }

  if (roles.length === 0) {
    return (
      <div className="flex min-h-80 flex-col items-center justify-center rounded-2xl border bg-card p-8 text-center" dir={direction}>
        <ShieldCheck className="h-12 w-12 text-muted-foreground" />

        <h3 className="mt-4 text-lg font-semibold">
          {t("rolesTable.emptyTitle")}
        </h3>

        <p className="mt-2 text-sm text-muted-foreground">
          {t("rolesTable.emptyDescription")}
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border bg-card shadow-sm" dir={direction}>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-start">
                {t("rolesTable.role")}
              </TableHead>

              <TableHead className="text-start">
                {t("rolesTable.permissions")}
              </TableHead>

              <TableHead className="text-right">
                {t("rolesTable.users")}
              </TableHead>

              <TableHead className="text-right">
                {t("rolesTable.status")}
              </TableHead>

              <TableHead className="text-right">
                {t("rolesTable.enabled")}
              </TableHead>

              <TableHead className="text-center">
                {t("rolesTable.actions")}
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
                            t("rolesTable.noDescription")}
                        </p>
                      </div>
                    </div>
                  </TableCell>

                  <TableCell>
                    <Badge variant="outline">
                      {t("rolesTable.permissionCount", { count: role.permissions.length })}
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
                        title={t("rolesTable.edit")}
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
                        title={t("rolesTable.delete")}
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