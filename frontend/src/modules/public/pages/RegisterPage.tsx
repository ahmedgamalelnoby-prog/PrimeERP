import {
  useState,
  type ChangeEvent,
  type FormEvent,
  type ReactNode,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import axios from "axios";
import toast from "react-hot-toast";

import { useTranslation } from "react-i18next";

import {
  Building2,
  CheckCircle2,
  Eye,
  EyeOff,
  Globe2,
  Loader2,
  LockKeyhole,
  Mail,
  Phone,
  User,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { registerCompany } from "../services/register.service";

import type {
  RegisterRequest,
} from "../types/register";

interface RegisterFormState {
  companyName: string;
  fullName: string;
  username: string;
  email: string;
  phone?: string;
  password: string;
  confirmPassword: string;
  acceptTerms: boolean;
}

const initialFormState = {
    companyName: "",
    fullName: "",
    username: "",
    email: "",
    mobile: "",
    password: "",
    confirmPassword: "",
    acceptTerms: false,
};

export default function RegisterPage() {
  const navigate = useNavigate();

  const {
    t,
    i18n,
  } = useTranslation();

  const currentLanguage =
    i18n.resolvedLanguage ??
    i18n.language;

  const isArabic =
    currentLanguage
      .toLowerCase()
      .startsWith("ar");

  const [formData, setFormData] =
    useState<RegisterFormState>(
      initialFormState,
    );

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [
    showConfirmPassword,
    setShowConfirmPassword,
  ] = useState(false);

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const changeLanguage = async () => {
    const newLanguage =
      isArabic ? "en" : "ar";

    await i18n.changeLanguage(
      newLanguage,
    );
  };

  const handleChange = (
    event: ChangeEvent<HTMLInputElement>,
  ) => {
    const {
      name,
      value,
      type,
      checked,
    } = event.target;

    setFormData((current) => ({
      ...current,

      [name]:
        type === "checkbox"
          ? checked
          : value,
    }));

    if (error) {
      setError("");
    }
  };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ) => {
    event.preventDefault();
    setError("");

    const companyName =
      formData.companyName.trim();

    const fullName =
      formData.fullName.trim();

    const username = formData.username
     .normalize("NFKC")
      .trim()
     .toLowerCase()
     .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_-]/g, "");

    const email =
      formData.email
        .trim()
        .toLowerCase();

    const mobile =
      formData.mobile.trim();

    if (!companyName) {
      setError(
        t(
          "register.errors.companyRequired",
        ),
      );

      return;
    }

    if (!fullName) {
      setError(
        t(
          "register.errors.fullNameRequired",
        ),
      );

      return;
    }

    if (!username) {
      setError("Username is required.");
      return;
    }

    if (!/^[a-z0-9_-]+$/.test(username)) {
      setError(
        "Username may contain letters, numbers, underscores and hyphens only.",
      );
      return;
    }

    if (!email) {
      setError(
        t(
          "register.errors.emailRequired",
        ),
      );

      return;
    }

    if (!mobile) {
      setError(
        t(
          "register.errors.mobileRequired",
        ),
      );

      return;
    }

    if (
      formData.password.length < 8
    ) {
      setError(
        t(
          "register.errors.passwordLength",
        ),
      );

      return;
    }

    const passwordByteLength =
      new TextEncoder().encode(
        formData.password,
      ).length;

    if (passwordByteLength > 72) {
      setError(
        "Password is too long. It must not exceed 72 bytes.",
      );
      return;
    }

    if (
      formData.password !==
      formData.confirmPassword
    ) {
      setError(
        t(
          "register.errors.passwordsMismatch",
        ),
      );

      return;
    }

    if (!formData.acceptTerms) {
      setError(
        t(
          "register.errors.termsRequired",
        ),
      );

      return;
    }

    const payload: RegisterRequest = {
  business_name: companyName,
  business_type: "other",
  owner_name: fullName,
  username,
  email,
  phone: mobile,
  password: formData.password,
  country_code: "EG",
  language: isArabic ? "ar" : "en",
  company_name: companyName,
  branch_name: isArabic
    ? "الفرع الرئيسي"
    : "Main Branch",
};

console.log("Registration payload:", payload);

    try {
      setIsLoading(true);

      await registerCompany(
        payload,
      );

      toast.success(
        t("register.success"),
      );

      navigate("/login", {
        replace: true,

        state: {
          registrationSuccess: true,
          email,
        },
      });
    } catch (
      submitError: unknown
    ) {
      console.error(
        "Registration failed:",
        submitError,
      );

      if (
        axios.isAxiosError(
          submitError,
        )
      ) {
        const responseData =
          submitError.response?.data;

        const responseMessage =
          responseData?.detail ??
          responseData?.message;

        if (
          typeof responseMessage ===
          "string"
        ) {
          setError(responseMessage);
          return;
        }

        if (
          Array.isArray(
            responseMessage,
          )
        ) {
          const firstError =
            responseMessage[0];

          if (
            typeof firstError?.msg ===
            "string"
          ) {
            setError(
              firstError.msg,
            );

            return;
          }
        }

        if (
          !submitError.response
        ) {
          setError(
            t(
              "register.errors.serverConnection",
            ),
          );

          return;
        }

        if (
          submitError.response
            .status === 409
        ) {
          setError(
            t(
              "register.errors.accountExists",
            ),
          );

          return;
        }

        if (
          submitError.response
            .status === 422
        ) {
          setError(
            t(
              "register.errors.invalidData",
            ),
          );

          return;
        }

        setError(
          t(
            "register.errors.registrationFailed",
          ),
        );

        return;
      }

      setError(
        t(
          "register.errors.unexpected",
        ),
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="grid min-h-screen lg:grid-cols-2">
        <section className="relative hidden overflow-hidden bg-slate-950 p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.28),transparent_45%)]" />

          <div className="relative z-10">
            <Link
              to="/"
              className="inline-flex items-center gap-3"
            >
              <div className="flex size-11 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-950/40">
                <Building2 className="size-6" />
              </div>

              <div>
                <p className="text-xl font-bold">
                  {t(
                    "common.appName",
                  )}
                </p>

                <p className="text-xs text-slate-400">
                  {t(
                    "common.appDescription",
                  )}
                </p>
              </div>
            </Link>
          </div>

          <div className="relative z-10 max-w-xl">
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
              {t(
                "register.featureTitle",
              )}
            </p>

            <h1 className="text-4xl font-bold leading-tight xl:text-5xl">
              {t(
                "register.heroTitle",
              )}
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
              {t(
                "register.heroDescription",
              )}
            </p>

            <div className="mt-10 space-y-5">
              <FeatureItem
                text={t(
                  "register.features.secure",
                )}
              />

              <FeatureItem
                text={t(
                  "register.features.branches",
                )}
              />

              <FeatureItem
                text={t(
                  "register.features.reports",
                )}
              />

              <FeatureItem
                text={t(
                  "register.features.trial",
                )}
              />
            </div>
          </div>

          <p className="relative z-10 text-sm text-slate-500">
            ©{" "}
            {new Date().getFullYear()}{" "}
            {t("common.appName")}.{" "}
            {t(
              "common.copyright",
            )}
          </p>
        </section>

        <section className="flex items-center justify-center px-5 py-10 sm:px-8 lg:px-12">
          <div className="w-full max-w-xl">
            <div className="mb-6 flex items-center justify-between">
              <Link
                to="/"
                className="inline-flex items-center gap-3 lg:hidden"
              >
                <div className="flex size-10 items-center justify-center rounded-xl bg-blue-600 text-white">
                  <Building2 className="size-5" />
                </div>

                <span className="text-xl font-bold text-slate-950">
                  {t(
                    "common.appName",
                  )}
                </span>
              </Link>

              <div className="ms-auto">
                <LanguageButton
                  isArabic={
                    isArabic
                  }
                  onClick={
                    changeLanguage
                  }
                />
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8">
              <div className="mb-8">
                <p className="text-sm font-semibold text-blue-600">
                  {t(
                    "register.workspaceLabel",
                  )}
                </p>

                <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
                  {t(
                    "register.pageTitle",
                  )}
                </h2>

                <p className="mt-3 text-sm leading-6 text-slate-500">
                  {t(
                    "register.pageSubtitle",
                  )}
                </p>
              </div>

              {error && (
                <div
                  role="alert"
                  className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
                >
                  {error}
                </div>
              )}

              <form
                onSubmit={
                  handleSubmit
                }
                className="space-y-5"
              >
                <div className="grid gap-5 sm:grid-cols-2">
                  <FormField
                    id="companyName"
                    label={t(
                      "register.companyName",
                    )}
                    icon={
                      <Building2 className="size-4" />
                    }
                  >
                    <Input
                      id="companyName"
                      name="companyName"
                      type="text"
                      value={
                        formData.companyName
                      }
                      onChange={
                        handleChange
                      }
                      placeholder={t(
                        "register.companyPlaceholder",
                      )}
                      autoComplete="organization"
                      disabled={
                        isLoading
                      }
                      required
                      className="h-11 ps-10"
                    />
                  </FormField>

                  <FormField
                    id="fullName"
                    label={t(
                      "register.fullName",
                    )}
                    icon={
                      <User className="size-4" />
                    }
                  >
                    <Input
                      id="fullName"
                      name="fullName"
                      type="text"
                      value={
                        formData.fullName
                      }
                      onChange={
                        handleChange
                      }
                      placeholder={t(
                        "register.fullNamePlaceholder",
                      )}
                      autoComplete="name"
                      disabled={
                        isLoading
                      }
                      required
                      className="h-11 ps-10"
                    />
                  </FormField>
                </div>

                <FormField
                  id="username"
                  label="Username"
                  icon={
                    <User className="size-4" />
                  }
                >
                  <Input
                    id="username"
                    name="username"
                    type="text"
                    value={
                      formData.username
                    }
                    onChange={
                      handleChange
                    }
                    placeholder="ahmed_gamal"
                    autoComplete="username"
                    pattern="[A-Za-z0-9_-]+"
                    title="Use letters, numbers, underscores, or hyphens only"
                    disabled={
                      isLoading
                    }
                    required
                    className="h-11 ps-10"
                  />
                </FormField>

                <FormField
                  id="email"
                  label={t(
                    "register.email",
                  )}
                  icon={
                    <Mail className="size-4" />
                  }
                >
                  <Input
                    id="email"
                    name="email"
                    type="email"
                    value={
                      formData.email
                    }
                    onChange={
                      handleChange
                    }
                    placeholder={t(
                      "register.emailPlaceholder",
                    )}
                    autoComplete="email"
                    disabled={
                      isLoading
                    }
                    required
                    className="h-11 ps-10"
                    dir="ltr"
                  />
                </FormField>

                <FormField
                  id="mobile"
                  label={t(
                    "register.mobile",
                  )}
                  icon={
                    <Phone className="size-4" />
                  }
                >
                  <Input
                    id="mobile"
                    name="mobile"
                    type="tel"
                    value={
                      formData.mobile
                    }
                    onChange={
                      handleChange
                    }
                    placeholder={t(
                      "register.mobilePlaceholder",
                    )}
                    autoComplete="tel"
                    disabled={
                      isLoading
                    }
                    required
                    className="h-11 ps-10"
                    dir="ltr"
                  />
                </FormField>

                <div className="grid gap-5 sm:grid-cols-2">
                  <PasswordField
                    id="password"
                    name="password"
                    label={t(
                      "register.password",
                    )}
                    value={
                      formData.password
                    }
                    placeholder={t(
                      "register.passwordPlaceholder",
                    )}
                    showPassword={
                      showPassword
                    }
                    disabled={
                      isLoading
                    }
                    onToggle={() =>
                      setShowPassword(
                        (current) =>
                          !current,
                      )
                    }
                    onChange={
                      handleChange
                    }
                    autoComplete="new-password"
                  />

                  <PasswordField
                    id="confirmPassword"
                    name="confirmPassword"
                    label={t(
                      "register.confirmPassword",
                    )}
                    value={
                      formData.confirmPassword
                    }
                    placeholder={t(
                      "register.confirmPasswordPlaceholder",
                    )}
                    showPassword={
                      showConfirmPassword
                    }
                    disabled={
                      isLoading
                    }
                    onToggle={() =>
                      setShowConfirmPassword(
                        (current) =>
                          !current,
                      )
                    }
                    onChange={
                      handleChange
                    }
                    autoComplete="new-password"
                  />
                </div>

                <label className="flex cursor-pointer items-start gap-3 text-sm text-slate-600">
                  <input
                    name="acceptTerms"
                    type="checkbox"
                    checked={
                      formData.acceptTerms
                    }
                    onChange={
                      handleChange
                    }
                    disabled={
                      isLoading
                    }
                    className="mt-1 size-4 rounded border-slate-300 accent-blue-600"
                  />

                  <span>
                    {t(
                      "register.acceptTerms",
                    )}{" "}
                    <Link
                      to="/terms"
                      className="font-semibold text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      {t(
                        "register.terms",
                      )}
                    </Link>{" "}
                    {t(
                      "register.and",
                    )}{" "}
                    <Link
                      to="/privacy"
                      className="font-semibold text-blue-600 hover:text-blue-700 hover:underline"
                    >
                      {t(
                        "register.privacy",
                      )}
                    </Link>
                    .
                  </span>
                </label>

                <Button
                  type="submit"
                  disabled={
                    isLoading
                  }
                  className="h-11 w-full"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />

                      {t(
                        "register.creatingAccount",
                      )}
                    </>
                  ) : (
                    t(
                      "register.startTrial",
                    )
                  )}
                </Button>
              </form>

              <div className="my-7 flex items-center gap-4">
                <div className="h-px flex-1 bg-slate-200" />

                <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
                  {t(
                    "register.alreadyRegistered",
                  )}
                </span>

                <div className="h-px flex-1 bg-slate-200" />
              </div>

              <p className="text-center text-sm text-slate-600">
                {t(
                  "register.alreadyHaveAccount",
                )}{" "}
                <Link
                  to="/login"
                  className="font-semibold text-blue-600 transition-colors hover:text-blue-700 hover:underline"
                >
                  {t(
                    "register.signIn",
                  )}
                </Link>
              </p>
            </div>

            <p className="mt-6 text-center text-xs text-slate-400">
              {t(
                "register.secureMessage",
              )}
            </p>
          </div>
        </section>
      </div>
    </main>
  );
}

interface FeatureItemProps {
  text: string;
}

function FeatureItem({
  text,
}: FeatureItemProps) {
  return (
    <div className="flex items-center gap-3 text-slate-200">
      <CheckCircle2 className="size-5 shrink-0 text-blue-400" />

      <span>{text}</span>
    </div>
  );
}

interface FormFieldProps {
  id: string;
  label: string;
  icon: ReactNode;
  children: ReactNode;
}

function FormField({
  id,
  label,
  icon,
  children,
}: FormFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
      </Label>

      <div className="relative">
        <span className="pointer-events-none absolute start-3 top-1/2 z-10 -translate-y-1/2 text-slate-400">
          {icon}
        </span>

        {children}
      </div>
    </div>
  );
}

interface PasswordFieldProps {
  id: string;
  name: string;
  label: string;
  value: string;
  placeholder: string;
  showPassword: boolean;
  autoComplete: string;
  disabled: boolean;

  onToggle: () => void;

  onChange: (
    event: ChangeEvent<HTMLInputElement>,
  ) => void;
}

function PasswordField({
  id,
  name,
  label,
  value,
  placeholder,
  showPassword,
  autoComplete,
  disabled,
  onToggle,
  onChange,
}: PasswordFieldProps) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>
        {label}
      </Label>

      <div className="relative">
        <LockKeyhole className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

        <Input
          id={id}
          name={name}
          type={
            showPassword
              ? "text"
              : "password"
          }
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          autoComplete={autoComplete}
          disabled={disabled}
          minLength={8}
          required
          className="h-11 ps-10 pe-10"
        />

        <button
          type="button"
          onClick={onToggle}
          disabled={disabled}
          aria-label={
            showPassword
              ? "Hide password"
              : "Show password"
          }
          className="absolute end-3 top-1/2 -translate-y-1/2 text-slate-400 transition-colors hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {showPassword ? (
            <EyeOff className="size-4" />
          ) : (
            <Eye className="size-4" />
          )}
        </button>
      </div>
    </div>
  );
}

interface LanguageButtonProps {
  isArabic: boolean;
  onClick: () => void;
}

function LanguageButton({
  isArabic,
  onClick,
}: LanguageButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex h-10 items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-slate-100"
    >
      <Globe2 className="size-4 text-blue-600" />

      {isArabic
        ? "English"
        : "العربية"}
    </button>
  );
}