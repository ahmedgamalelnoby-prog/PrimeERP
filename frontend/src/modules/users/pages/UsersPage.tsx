import {
  Plus,
  Search,
  UserRound,
} from "lucide-react";
import {
  useMemo,
  useState,
} from "react";

import PageHeader from "@/components/layout/PageHeader";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import ResetPasswordDialog from "../components/ResetPasswordDialog";
import UserForm from "../components/UserForm";
import UserTable from "../components/UserTable";
import { useUsers } from "../hooks/useUsers";
import type { User } from "../types/user";

export default function UsersPage() {
  const {
  users,
  meta,
  loading,
  processingId,
  filters,
  setFilters,
  reload,
  goToPage,
  changePageSize,
  createUser,
  updateUser,
  toggleStatus,
  deleteUser,
} = useUsers();

  const [formOpen, setFormOpen] =
    useState(false);

  const [selectedUser, setSelectedUser] =
    useState<User | null>(null);

  const [
    resetPasswordUser,
    setResetPasswordUser,
  ] = useState<User | null>(null);

  const totalUsers = meta.total;

  const activeUsers = useMemo(
    () =>
      users.filter(
        (user) => user.is_active,
      ).length,
    [users],
  );

  const handleNewUser = () => {
    setSelectedUser(null);
    setFormOpen(true);
  };

  const handleEdit = (user: User) => {
    setSelectedUser(user);
    setFormOpen(true);
  };

  const handleDelete = async (
    user: User,
  ) => {
    const confirmed = window.confirm(
      `هل تريد حذف المستخدم "${
        user.full_name || user.username
      }"؟`,
    );

    if (!confirmed) {
      return;
    }

    await deleteUser(user);
  };

  return (
    <div className="space-y-6" dir="rtl">
      <PageHeader
        title="إدارة المستخدمين"
        description="إضافة المستخدمين وتعديل بياناتهم والتحكم في حالتهم وأدوارهم."
        actions={
          <Button
            type="button"
            onClick={handleNewUser}
          >
            <Plus className="ml-2 h-4 w-4" />
            مستخدم جديد
          </Button>
        }
      />

      <section className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
              <UserRound className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-muted-foreground">
                إجمالي المستخدمين
              </p>

              <p className="text-2xl font-bold">
                {totalUsers}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-card p-5 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-600">
              <UserRound className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-muted-foreground">
                المستخدمون النشطون
              </p>

              <p className="text-2xl font-bold">
                {activeUsers}
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border bg-card p-4 shadow-sm">
        <div className="relative max-w-md">
          <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

          <Input
            value={filters.search || ""}
            onChange={(event) =>
              setFilters((current) => ({
                ...current,
                search:
                  event.target.value,
                page: 1,
              }))
            }
            placeholder="البحث بالاسم أو اسم المستخدم أو البريد..."
            className="pr-10"
          />
        </div>
      </section>

      <UserTable
        users={users}
        loading={loading}
        processingId={processingId}
        onEdit={handleEdit}
        onDelete={handleDelete}
        onToggleStatus={toggleStatus}
        onResetPassword={(user) =>
          setResetPasswordUser(user)
        }
      />

      <UserForm
        open={formOpen}
        user={selectedUser}
        loading={
          selectedUser
            ? processingId ===
              selectedUser.id
            : false
        }
        onOpenChange={(open) => {
          setFormOpen(open);

          if (!open) {
            setSelectedUser(null);
          }
        }}
        onCreate={createUser}
        onUpdate={updateUser}
      />

      <ResetPasswordDialog
        open={Boolean(resetPasswordUser)}
        user={resetPasswordUser}
        onOpenChange={(open) => {
          if (!open) {
            setResetPasswordUser(null);
          }
        }}
        onSuccess={reload}
      />
    </div>
  );
}