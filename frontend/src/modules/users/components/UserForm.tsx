import { Loader2 } from "lucide-react";
import {
  type FormEvent,
  useEffect,
  useState,
} from "react";
import { useTranslation } from "react-i18next";

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
} : UserFormProps) {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();
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
      alert(t("userForm.errors.fullName"));
      return false;
    }

    if (!form.username.trim()) {
      alert(t("userForm.errors.username"));
      return false;
    }

    if (form.username.trim().length < 3) {
      alert(
        t("userForm.errors.usernameLength"),
      );
      return false;
    }

    if (!form.email.trim()) {
      alert(t("userForm.errors.email"));
      return false;
    }

    if (!isEditing && !form.password) {
      alert(t("userForm.errors.password"));
      return false;
    }

    if (
      form.password &&
      form.password.length < 8
    ) {
      alert(
        t("userForm.errors.passwordLength"),
      );
      return false;
    }

    if (
      form.password &&
      form.password.length > 128
    ) {
      alert(
        t("userForm.errors.passwordMax"),
      );
      return false;
    }

    if (
      form.password !== form.confirmPassword
    ) {
      alert(t("userForm.errors.passwordMismatch"));
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
        dir={direction}
      >
        <DialogHeader className="text-start">
          <DialogTitle>
            {isEditing
              ? t("userForm.titleEdit")
              : t("userForm.titleCreate")}
          </DialogTitle>

          <DialogDescription>
            {isEditing
              ? t("userForm.descriptionEdit")
              : t("userForm.descriptionCreate")}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={handleSubmit}
          className="space-y-6"
        >
          <div className="grid gap-4 sm:grid-cols-2">
            {/* {t("userForm.fullName")} */}
            <div className="space-y-2">
              <Label htmlFor="full_name">
                {t("userForm.fullName")} *
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
                placeholder={t("userForm.fullNamePlaceholder")}
                autoComplete="name"
                required
              />
            </div>

            {/* {t("userForm.username")} */}
            <div className="space-y-2">
              <Label htmlFor="username">
                {t("userForm.username")} *
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

            {/* {t("userForm.email")} */}
            <div className="space-y-2">
              <Label htmlFor="email">
                {t("userForm.email")} *
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

            {/* {t("userForm.phone")} */}
            <div className="space-y-2">
              <Label htmlFor="phone">
                {t("userForm.phone")}
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
                  ? t("userForm.newPassword")
                  : t("userForm.password") + " *"}
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
                    ? t("userForm.passwordPlaceholderEdit")
                    : t("userForm.passwordPlaceholderCreate")
                }
                autoComplete="new-password"
                minLength={
                  form.password ? 8 : undefined
                }
                maxLength={128}
                required={!isEditing}
              />

              <p className="text-xs text-muted-foreground">
                {t("userForm.passwordHint")}
              </p>
            </div>

            {/* تأكيد كلمة المرور */}
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">
                {isEditing
                  ? t("userForm.confirmNewPassword")
                  : t("userForm.confirmPassword") + " *"}
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
                placeholder={t("userForm.confirmPasswordPlaceholder")}
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

            {/* {t("userForm.role")} */}
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="role_id">
                {t("userForm.role")}
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
                        ? t("userForm.loadingRoles")
                        : t("userForm.chooseRole")
                    }
                  />
                </SelectTrigger>

                <SelectContent>
                  <SelectItem value="none">
                    {t("userForm.noRole")}
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
                    {t("userForm.noRoles")}
                  </p>
                )}
            </div>

            {/* {t("userForm.address")} */}
            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="address">
                {t("userForm.address")}
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
                placeholder={t("userForm.addressPlaceholder")}
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
                <Loader2 className="ms-2 h-4 w-4 animate-spin" />
              )}

              {isEditing
                ? t("userForm.saveChanges")
                : t("userForm.create")}
            </Button>

            <Button
              type="button"
              variant="outline"
              onClick={() => {
                handleDialogChange(false);
              }}
              disabled={loading}
            >
              {t("common.cancel")}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}