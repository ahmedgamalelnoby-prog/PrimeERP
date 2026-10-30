import {
  Plus,
  Search,
  ShieldCheck,
  Users,
} from "lucide-react";

import {
  useMemo,
  useState,
} from "react";

import PageHeader from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import RoleForm from "../components/RoleForm";
import RoleTable from "../components/RoleTable";
import { useRoles } from "../hooks/useRoles";
import type { Role } from "../types/role";
import { useTranslation } from "react-i18next";

export default function RolesPage() {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
  const {
    roles,
    permissions,
    loading,
    permissionsLoading,
    processingId,
    filters,
    setFilters,
    createRole,
    updateRole,
    toggleStatus,
    deleteRole,
  } = useRoles();

  const [formOpen, setFormOpen] =
    useState(false);

  const [selectedRole, setSelectedRole] =
    useState<Role | null>(null);

  const activeRoles = useMemo(
    () =>
      roles.filter(
        (role) => role.is_active,
      ).length,
    [roles],
  );

  const usersAssigned = useMemo(
    () =>
      roles.reduce(
        (total, role) =>
          total + role.users_count,
        0,
      ),
    [roles],
  );

  const handleNewRole = () => {
    setSelectedRole(null);
    setFormOpen(true);
  };

  const handleEditRole = (
    role: Role,
  ) => {
    setSelectedRole(role);
    setFormOpen(true);
  };

  const handleDeleteRole = async (
    role: Role,
  ) => {
    if (role.users_count > 0) {
      window.alert(
        t("roles.errors.deleteAssigned", { count: role.users_count }),
      );
      return;
    }

    const confirmed =
      window.confirm(
        t("roles.confirmDelete", { name: role.name }),
      );

    if (!confirmed) {
      return;
    }

    await deleteRole(role);
  };

  return (
    <div className="space-y-6" dir={direction}>
      <PageHeader
        title={t("roles.title")}
        description={t("roles.description")}
        actions={
          <Button
            type="button"
            onClick={handleNewRole}
          >
            <Plus className="me-2 h-4 w-4" />
            {t("roles.newRole")}
          </Button>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <ShieldCheck className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-muted-foreground">
                {t("roles.total")}
              </p>

              <p className="text-2xl font-bold">
                {roles.length}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
              <ShieldCheck className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-muted-foreground">
                {t("roles.active")}
              </p>

              <p className="text-2xl font-bold">
                {activeRoles}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-card p-5 shadow-sm sm:col-span-2 xl:col-span-1">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-500/10 text-blue-600">
              <Users className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-muted-foreground">
                {t("roles.assignedUsers")}
              </p>

              <p className="text-2xl font-bold">
                {usersAssigned}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

          <Input
            value={filters.search || ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                search:
                  event.target.value,
              }))
            }
            placeholder={t("roles.searchPlaceholder")}
            className="ps-10"
          />
        </div>
      </section>

      <RoleTable
        roles={roles}
        loading={loading}
        processingId={processingId}
        onEdit={handleEditRole}
        onDelete={handleDeleteRole}
        onToggleStatus={toggleStatus}
      />

      <RoleForm
        open={formOpen}
        role={selectedRole}
        permissions={permissions}
        permissionsLoading={
          permissionsLoading
        }
        loading={
          selectedRole
            ? processingId ===
              selectedRole.id
            : false
        }
        onOpenChange={(open) => {
          setFormOpen(open);

          if (!open) {
            setSelectedRole(null);
          }
        }}
        onCreate={createRole}
        onUpdate={updateRole}
      />
    </div>
  );
}