import { Loader2 } from "lucide-react";
import {
  type FormEvent,
  useEffect,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { rolesService } from "../services/roles.service";
import type { Role } from "../types/role";
import type {
  User,
  UserCreatePayload,
  UserUpdatePayload,
} from "../types/user";

interface UserFormProps {
  open: boolean;
  user: User | null;
  loading?: boolean;

  onOpenChange: (open: boolean) => void;

  onCreate: (
    payload: UserCreatePayload,
  ) => Promise<boolean>;

  onUpdate: (
    id: number,
    payload: UserUpdatePayload,
  ) => Promise<boolean>;
}

interface FormState {
  username: string;
  email: string;
  password: string;
  confirmPassword: string;
  full_name: string;
  phone: string;
  address: string;
  role_id: string;
}

const initialState: FormState = {
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
  full_name: "",
  phone: "",
  address: "",
  role_id: "none",
};

export default function UserForm({
  open,
  user,
  loading = false,
  onOpenChange,
  onCreate,
  onUpdate,
}: UserFormProps) {
  const [form, setForm] =
    useState<FormState>(initialState);

  const [roles, setRoles] = useState<Role[]>([]);
  const [rolesLoading, setRolesLoading] =
    useState(false);

  const isEditing = Boolean(user);

  useEffect(() => {
    if (!open) {
      return;
    }

    if (user) {
      setForm({
        username: user.username || "",
        email: user.email || "",
        password: "",
        confirmPassword: "",
        full_name: user.full_name || "",
        phone: user.phone || "",
        address: user.address || "",
        role_id:
          user.role_id !== null &&
          user.role_id !== undefined
            ? String(user.role_id)
            : "none",
      });
    } else {
      setForm(initialState);
    }
  }, [open, user]);

  useEffect(() => {
    if (!open) {
      return;
    }

    const loadRoles = async () => {
      try {
        setRolesLoading(true);

        const data = await rolesService.getAll();

        setRoles(
          data.filter(
            (role) => role.is_active !== false,
          ),
        );
      } catch (error) {
        console.error(
          "Failed to load roles:",
          error,
        );

        setRoles([]);
      } finally {
        setRolesLoading(false);
      }
    };

    void loadRoles();
  }, [open]);

  const updateField = <
    K extends keyof FormState,
  >(
    field: K,
    value: FormState[K],
  ) => {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  };

  const validateForm = (): boolean => {
    if (!form.full_name.trim()) {
      alert("برجاء إدخال الاسم بالكامل.");
      return false;
    }

    if (!form.username.trim()) {
      alert("برجاء إدخال اسم المستخدم.");
      return false;
    }

    if (form.username.trim().length < 3) {
      alert(
        "يجب أن يتكون اسم المستخدم من 3 أحرف على الأقل.",
      );
      return false;
    }

    if (!form.email.trim()) {
      alert("برجاء إدخال البريد الإلكتروني.");
      return false;
    }

    if (!isEditing && !form.password) {
      alert("برجاء إدخال كلمة المرور.");
      return false;
    }

    if (
      form.password &&
      form.password.length < 8
    ) {
      alert(
        "يجب أن تتكون كلمة المرور من 8 أحرف على الأقل.",
      );
      return false;
    }

    if (
      form.password &&
      form.password.length > 128
    ) {
      alert(
        "يجب ألا تزيد كلمة المرور عن 128 حرفًا.",
      );
      return false;
    }

    if (
      form.password !== form.confirmPassword
    ) {
      alert("كلمتا المرور غير متطابقتين.");
      return false;
    }

    return true;
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    const commonPayload = {
      username: form.username.trim(),
      email: form.email.trim(),

      full_name:
        form.full_name.trim() || undefined,

      phone:
        form.phone.trim() || undefined,

      address:
        form.address.trim() || undefined,

      role_id:
        form.role_id === "none"
          ? null
          : Number(form.role_id),

      // القيم الافتراضية بعد حذفها من الفورم
      is_active: true,
      is_superuser: false,
      must_change_password: false,
    };

    let success = false;

    if (user) {
      const updatePayload: UserUpdatePayload = {
        ...commonPayload,
      };

      if (form.password) {
        updatePayload.password = form.password;
      }

      console.log(
        "Update user payload:",
        updatePayload,
      );

      success = await onUpdate(
        user.id,
        updatePayload,
      );
    } else {
      const createPayload: UserCreatePayload = {
        ...commonPayload,
        password: form.password,

        // لا يتم إنشاء المستخدم كمدير منصة
        is_platform_admin: false,
      };

      console.log(
        "Create user payload:",
        createPayload,
      );

      success = await onCreate(createPayload);
    }

    if (success) {
      onOpenChange(false);
      setForm(initialState);
    }
  };

  const handleDialogChange = (
    newOpen: boolean,
  ) => {
    if (loading) {
      return;
    }

    onOpenChange(newOpen);

    if (!newOpen) {
      setForm(initialState);
    }
  };

  return (
    <Dialog
      open={open}
      onOpenChange={handleDialogChange}
    >
      <DialogContent
        className="max-h-[90vh] overflow-y-auto sm:max-w-2xl"
        dir="rtl"
      >
        <DialogHeader className="text-right">
          <DialogTitle>
            {isEditing
              ? "تعديل المستخدم"
              : "إضافة مستخدم جديد"}
          </DialogTitle>

          <DialogDescription>
            {isEditing
              ? "عدّل بيانات المستخدم ثم اضغط حفظ التعديلات."
              : "أدخل بيانات المستخدم وحدد الدور والصلاحيات."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            {/* الاسم بالكامل */}
            <div className="space-y-2">
              <Label htmlFor="full_name">
                الاسم بالكامل *
              </Label>

              <Input
                id="full_name"
                name="full_name"
                value={form.full_name}
                onChange={(event) => {
                  updateField(
                    "full_name",
                    event.target.value,
                  );
                }}
                placeholder="أحمد محمد"
                autoComplete="name"
                required
              />
            </div>

            {/* اسم المستخدم */}
            <div className="space-y-2">
              <Label htmlFor="username">
                اسم المستخدم *
              </Label>

              <Input
                id="username"
                name="username"
                value={form.username}
                onChange={(event) => {
                  updateField(
                    "username",
                    event.target.value,
                  );
                }}
                placeholder="ahmed"
                autoComplete="username"
                minLength={3}
                maxLength={50}
                required
              />
            </div>

            {/* البريد الإلكتروني */}
            <div className="space-y-2">
              <Label htmlFor="email">
                البريد الإلكتروني *
              </Label>

              <Input
                id="email"
                name="email"
                type="email"
                value={form.email}
                onChange={(event) => {
                  updateField(
                    "email",
                    event.target.value,
                  );
                }}
                placeholder="user@primeerp.com"
                autoComplete="email"
                required
              />
            </div>

            {/* رقم الهاتف */}
            <div className="space-y-2">
              <Label htmlFor="phone">
                رقم الهاتف
              </Label>

              <Input
                id="phone"
                name="phone"
                type="tel"
                value={form.phone}
                onChange={(event) => {
                  updateField(
                    "phone",
                    event.target.value,
                  );
                }}
                placeholder="01xxxxxxxxx"
                autoComplete="tel"
                maxLength={30}
              />
            </div>

            {/* كلمة المرور */}
            <div className="space-y-2">
              <Label htmlFor="password">
                {isEditing
                  ? "كلمة مرور جديدة"
                  : "كلمة المرور *"}
              </Label>

              <Input
                id="password"
                name="password"
                type="password"
                value={form.password}
                onChange={(event) => {
                  updateField(
                    "password",
                    event.target.value,
                  );
                }}
                placeholder={
                  isEditing
                    ? "اتركها فارغة دون تغيير"
                    : "8 أحرف على الأقل"
                }
                autoComplete="new-password"
                minLength={
                  form.password ? 8 : undefined
                }
                maxLength={128}
                required={!isEditing}
              />

              <p className="text-xs text-muted-foreground">
                يجب أن تتكون كلمة المرور من 8 أحرف
                على الأقل.
              </p>
            </div>

            {/* تأكيد كلمة المرور */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">
                {isEditing
                  ? "تأكيد كلمة المرور الجديدة"
                  : "تأكيد كلمة المرور *"}
              </Label>

              <Input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                value={form.confirmPassword}
                onChange={(event) => {
                  updateField(
                    "confirmPassword",
                    event.target.value,
                  );
                }}
                placeholder="أعد إدخال كلمة المرور"
                autoComplete="new-password"
                minLength={
                  form.confirmPassword
                    ? 8
                    : undefined
                }
                maxLength={128}
                required={
                  !isEditing ||
                  Boolean(form.password)
                }
              />
            </div>

            {/* الدور والصلاحيات */}
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="role_id">
                الدور والصلاحيات
              </Label>

              <Select
                value={form.role_id}
                onValueChange={(value) => {
                  updateField(
                    "role_id",
                    value,
                  );
                }}
                disabled={
                  rolesLoading || loading
                }
              >
                <SelectTrigger id="role_id">
                  <SelectValue
                    placeholder={
                      rolesLoading
                        ? "جاري تحميل الأدوار..."
                        : "اختر الدور"
                    }
                  />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="none">
                    بدون دور
                  </SelectItem>

                  {roles.map((role) => (
                    <SelectItem
                      key={role.id}
                      value={String(role.id)}
                    >
                      {role.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {!rolesLoading &&
                roles.length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    لا توجد أدوار متاحة حاليًا.
                  </p>
                )}
            </div>

            {/* العنوان */}
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="address">
                العنوان
              </Label>

              <Input
                id="address"
                name="address"
                value={form.address}
                onChange={(event) => {
                  updateField(
                    "address",
                    event.target.value,
                  );
                }}
                placeholder="أدخل عنوان المستخدم"
                autoComplete="street-address"
              />
            </div>
          </div>

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
                : "إضافة المستخدم"}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() => {
                handleDialogChange(false);
              }}
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