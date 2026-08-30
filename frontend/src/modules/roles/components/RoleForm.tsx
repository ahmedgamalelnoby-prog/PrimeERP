import {
  CheckCheck,
  Loader2,
  Search,
  ShieldCheck,
} from "lucide-react";

import {
  type FormEvent,
  useEffect,
  useMemo,
  useState,
} from "react";

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

import type {
  Permission,
  Role,
  RoleCreatePayload,
  RoleUpdatePayload,
} from "../types/role";

interface RoleFormProps {
  open: boolean;
  role: Role | null;
  permissions: Permission[];
  permissionsLoading: boolean;
  loading?: boolean;

  onOpenChange: (open: boolean) => void;

  onCreate: (
    payload: RoleCreatePayload,
  ) => Promise<boolean>;

  onUpdate: (
    id: number,
    payload: RoleUpdatePayload,
  ) => Promise<boolean>;
}

interface FormState {
  name: string;
  description: string;
  is_active: boolean;
  permission_ids: number[];
}

const initialState: FormState = {
  name: "",
  description: "",
  is_active: true,
  permission_ids: [],
};

const resourceNames: Record<string, string> = {
  users: "المستخدمون",
  roles: "الأدوار",
  permissions: "الصلاحيات",
  companies: "الشركات",
  branches: "الفروع",
  sales: "المبيعات",
  customers: "العملاء",
  suppliers: "الموردون",
  products: "المنتجات",
  inventory: "المخزون",
  purchasing: "المشتريات",
  accounting: "الحسابات",
  restaurant: "المطاعم",
  pos: "نقاط البيع",
  hr: "الموارد البشرية",
  reports: "التقارير",
  shipping: "شركات الشحن",
  settings: "الإعدادات",
};

const actionNames: Record<string, string> = {
  view: "عرض",
  read: "عرض",
  create: "إضافة",
  update: "تعديل",
  delete: "حذف",
  approve: "اعتماد",
  manage: "إدارة كاملة",
  print: "طباعة",
  export: "تصدير",
  cancel: "إلغاء",
};

export default function RoleForm({
  open,
  role,
  permissions,
  permissionsLoading,
  loading = false,
  onOpenChange,
  onCreate,
  onUpdate,
}: RoleFormProps) {
  const [form, setForm] =
    useState<FormState>(initialState);

  const [permissionSearch, setPermissionSearch] =
    useState("");

  const isEditing = Boolean(role);

  useEffect(() => {
    if (!open) {
      return;
    }

    setPermissionSearch("");

    if (role) {
      setForm({
        name: role.name,
        description:
          role.description || "",
        is_active: role.is_active,
        permission_ids:
          role.permissions.map(
            (permission) =>
              permission.id,
          ),
      });
    } else {
      setForm(initialState);
    }
  }, [open, role]);

  const filteredPermissions = useMemo(() => {
    const search =
      permissionSearch
        .trim()
        .toLowerCase();

    if (!search) {
      return permissions;
    }

    return permissions.filter(
      (permission) =>
        permission.name
          .toLowerCase()
          .includes(search) ||
        permission.resource
          .toLowerCase()
          .includes(search) ||
        permission.action
          .toLowerCase()
          .includes(search) ||
        permission.description
          ?.toLowerCase()
          .includes(search),
    );
  }, [permissionSearch, permissions]);

  const groupedPermissions = useMemo(() => {
    return filteredPermissions.reduce<
      Record<string, Permission[]>
    >((groups, permission) => {
      const resource =
        permission.resource ||
        "other";

      if (!groups[resource]) {
        groups[resource] = [];
      }

      groups[resource].push(permission);

      return groups;
    }, {});
  }, [filteredPermissions]);

  const togglePermission = (
    permissionId: number,
  ) => {
    setForm((current) => ({
      ...current,
      permission_ids:
        current.permission_ids.includes(
          permissionId,
        )
          ? current.permission_ids.filter(
              (id) =>
                id !== permissionId,
            )
          : [
              ...current.permission_ids,
              permissionId,
            ],
    }));
  };

  const selectResource = (
    resourcePermissions: Permission[],
  ) => {
    const resourceIds =
      resourcePermissions.map(
        (permission) =>
          permission.id,
      );

    const allSelected =
      resourceIds.every((id) =>
        form.permission_ids.includes(id),
      );

    setForm((current) => ({
      ...current,
      permission_ids: allSelected
        ? current.permission_ids.filter(
            (id) =>
              !resourceIds.includes(id),
          )
        : Array.from(
            new Set([
              ...current.permission_ids,
              ...resourceIds,
            ]),
          ),
    }));
  };

  const selectAll = () => {
    const allIds = permissions.map(
      (permission) => permission.id,
    );

    const allSelected =
      allIds.every((id) =>
        form.permission_ids.includes(id),
      );

    setForm((current) => ({
      ...current,
      permission_ids: allSelected
        ? []
        : allIds,
    }));
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!form.name.trim()) {
      return;
    }

    const payload = {
      name: form.name.trim(),
      description:
        form.description.trim() ||
        null,
      is_active: form.is_active,
      permission_ids:
        form.permission_ids,
    };

    const success = role
      ? await onUpdate(role.id, payload)
      : await onCreate(payload);

    if (success) {
      onOpenChange(false);
      setForm(initialState);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <DialogContent
        className="max-h-[92vh] overflow-y-auto sm:max-w-4xl"
        dir="rtl"
      >
        <DialogHeader className="text-right">
          <DialogTitle>
            {isEditing
              ? "تعديل الدور"
              : "إضافة دور جديد"}
          </DialogTitle>

          <DialogDescription>
            حدد اسم الدور والصلاحيات التي سيتم
            منحها للمستخدمين المرتبطين به.
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="role-name">
                اسم الدور *
              </Label>

              <Input
                id="role-name"
                value={form.name}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    name:
                      event.target.value,
                  }))
                }
                placeholder="مثال: مدير الفرع"
                required
              />
            </div>

            <div className="flex items-end">
              <div className="flex w-full items-center justify-between rounded-xl border p-3">
                <Label htmlFor="role-active">
                  الدور نشط
                </Label>

                <Switch
                  id="role-active"
                  checked={form.is_active}
                  onCheckedChange={(checked) =>
                    setForm((current) => ({
                      ...current,
                      is_active: checked,
                    }))
                  }
                />
              </div>
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="role-description">
                الوصف
              </Label>

              <Input
                id="role-description"
                value={form.description}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    description:
                      event.target.value,
                  }))
                }
                placeholder="وصف مختصر لمسؤوليات هذا الدور"
              />
            </div>
          </div>

          <section className="rounded-2xl border">
            <div className="flex flex-col justify-between gap-4 border-b p-4 sm:flex-row sm:items-center">
              <div>
                <h3 className="flex items-center gap-2 font-semibold">
                  <ShieldCheck className="h-5 w-5 text-primary" />
                  صلاحيات الدور
                </h3>

                <p className="mt-1 text-xs text-muted-foreground">
                  تم اختيار{" "}
                  {form.permission_ids.length} من{" "}
                  {permissions.length} صلاحية
                </p>
              </div>

              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={selectAll}
              >
                <CheckCheck className="ml-2 h-4 w-4" />
                تحديد أو إلغاء الكل
              </Button>
            </div>

            <div className="border-b p-4">
              <div className="relative">
                <Search className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

                <Input
                  value={permissionSearch}
                  onChange={(event) =>
                    setPermissionSearch(
                      event.target.value,
                    )
                  }
                  placeholder="البحث في الصلاحيات..."
                  className="pr-10"
                />
              </div>
            </div>

            <div className="max-h-[420px] space-y-4 overflow-y-auto p-4">
              {permissionsLoading ? (
                <div className="flex min-h-40 items-center justify-center">
                  <Loader2 className="h-7 w-7 animate-spin text-primary" />
                </div>
              ) : Object.keys(
                  groupedPermissions,
                ).length === 0 ? (
                <div className="py-12 text-center">
                  <ShieldCheck className="mx-auto h-10 w-10 text-muted-foreground" />

                  <p className="mt-3 text-sm text-muted-foreground">
                    لا توجد صلاحيات متاحة.
                  </p>
                </div>
              ) : (
                Object.entries(
                  groupedPermissions,
                ).map(
                  ([
                    resource,
                    resourcePermissions,
                  ]) => {
                    const allSelected =
                      resourcePermissions.every(
                        (permission) =>
                          form.permission_ids.includes(
                            permission.id,
                          ),
                      );

                    return (
                      <div
                        key={resource}
                        className="rounded-xl border bg-muted/20"
                      >
                        <div className="flex items-center justify-between border-b px-4 py-3">
                          <div>
                            <h4 className="text-sm font-semibold">
                              {resourceNames[
                                resource
                              ] || resource}
                            </h4>

                            <p className="mt-1 text-xs text-muted-foreground">
                              {
                                resourcePermissions.length
                              }{" "}
                              صلاحية
                            </p>
                          </div>

                          <button
                            type="button"
                            onClick={() =>
                              selectResource(
                                resourcePermissions,
                              )
                            }
                            className="text-xs font-medium text-primary hover:underline"
                          >
                            {allSelected
                              ? "إلغاء تحديد القسم"
                              : "تحديد القسم بالكامل"}
                          </button>
                        </div>

                        <div className="grid gap-2 p-3 sm:grid-cols-2">
                          {resourcePermissions.map(
                            (permission) => {
                              const checked =
                                form.permission_ids.includes(
                                  permission.id,
                                );

                              return (
                                <label
                                  key={
                                    permission.id
                                  }
                                  className={[
                                    "flex cursor-pointer items-start gap-3 rounded-xl border p-3 transition-colors",
                                    checked
                                      ? "border-primary/40 bg-primary/5"
                                      : "hover:bg-muted/50",
                                  ].join(" ")}
                                >
                                  <input
                                    type="checkbox"
                                    checked={
                                      checked
                                    }
                                    onChange={() =>
                                      togglePermission(
                                        permission.id,
                                      )
                                    }
                                    className="mt-1 h-4 w-4 accent-primary"
                                  />

                                  <div>
                                    <p className="text-sm font-medium">
                                      {actionNames[
                                        permission
                                          .action
                                      ] ||
                                        permission.action}
                                    </p>

                                    <p className="mt-1 text-xs text-muted-foreground">
                                      {permission.description ||
                                        permission.name}
                                    </p>
                                  </div>
                                </label>
                              );
                            },
                          )}
                        </div>
                      </div>
                    );
                  },
                )
              )}
            </div>
          </section>

          <DialogFooter className="gap-2 sm:justify-start">
            <Button
              type="submit"
              disabled={loading}
            >
              {loading && (
                <Loader2 className="ml-2 h-4 w-4 animate-spin" />
              )}

              {isEditing
                ? "حفظ التعديلات"
                : "إنشاء الدور"}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() =>
                onOpenChange(false)
              }
              disabled={loading}
            >
              إلغاء
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}