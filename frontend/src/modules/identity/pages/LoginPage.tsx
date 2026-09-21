import {
  useEffect,
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  useLocation,
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
  UserRound,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useAuth } from "@/modules/identity/hooks/useAuth";

interface LoginLocationState {
  registrationSuccess?: boolean;
  username?: string;
}

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    t,
    i18n,
  } = useTranslation();

  const { login } = useAuth();

  const locationState =
    location.state as
      | LoginLocationState
      | null;

  const currentLanguage =
    i18n.resolvedLanguage ??
    i18n.language;

  const isArabic =
    currentLanguage
      .toLowerCase()
      .startsWith("ar");

  const [
    loginValue,
    setLoginValue,
  ] = useState(
    locationState?.username ?? "",
  );

  const [
    password,
    setPassword,
  ] = useState("");

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);

  const [
    rememberMe,
    setRememberMe,
  ] = useState(false);

  const [
    isLoading,
    setIsLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  useEffect(() => {
    const savedLogin =
      localStorage.getItem(
        "primeerp_remember_login",
      );

    if (
      !locationState?.username &&
      savedLogin
    ) {
      setLoginValue(savedLogin);
      setRememberMe(true);
    }
  }, [locationState?.username]);

  useEffect(() => {
    if (
      locationState
        ?.registrationSuccess
    ) {
      toast.success(
        t(
          "login.registrationSuccess",
        ),
      );

      navigate("/login", {
        replace: true,
        state: null,
      });
    }
  }, [
    locationState
      ?.registrationSuccess,
    navigate,
    t,
  ]);

  const changeLanguage =
    async (): Promise<void> => {
      const newLanguage =
        isArabic ? "en" : "ar";

      await i18n.changeLanguage(
        newLanguage,
      );
    };

  const handleSubmit = async (
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    event.preventDefault();
    setError("");

    const normalizedLogin =
      loginValue.trim();

    if (
      !normalizedLogin ||
      !password
    ) {
      setError(
        t(
          "login.errors.required",
        ),
      );

      return;
    }

    try {
      setIsLoading(true);

      await login(
        normalizedLogin,
        password,
      );

      if (rememberMe) {
        localStorage.setItem(
          "primeerp_remember_login",
          normalizedLogin,
        );
      } else {
        localStorage.removeItem(
          "primeerp_remember_login",
        );
      }

      toast.success(
        t("login.success"),
      );

      navigate(
        "/dashboard",
        {
          replace: true,
        },
      );
    } catch (
      loginError: unknown
    ) {
      console.error(
        "Login failed:",
        loginError,
      );

      if (
        axios.isAxiosError(
          loginError,
        )
      ) {
        if (
          !loginError.response
        ) {
          setError(
            t(
              "login.errors.serverConnection",
            ),
          );

          return;
        }

        if (
          loginError.response
            .status === 401 ||
          loginError.response
            .status === 400
        ) {
          setError(
            t(
              "login.errors.invalidCredentials",
            ),
          );

          return;
        }

        if (
          loginError.response
            .status === 403
        ) {
          const responseDetail =
            loginError.response.data
              ?.detail;

          setError(
            typeof responseDetail ===
              "string"
              ? responseDetail
              : t(
                  "login.errors.inactiveAccount",
                ),
          );

          return;
        }

        if (
          loginError.response
            .status === 422
        ) {
          setError(
            t(
              "login.errors.invalidRequest",
            ),
          );

          return;
        }
      }

      setError(
        t(
          "login.errors.unexpected",
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
                "login.welcomeBack",
              )}
            </p>

            <h1 className="text-4xl font-bold leading-tight xl:text-5xl">
              {t(
                "login.heroTitle",
              )}
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
              {t(
                "login.heroDescription",
              )}
            </p>

            <div className="mt-10 space-y-5">
              <FeatureItem
                text={t(
                  "login.features.dashboard",
                )}
              />

              <FeatureItem
                text={t(
                  "login.features.security",
                )}
              />

              <FeatureItem
                text={t(
                  "login.features.reporting",
                )}
              />

              <FeatureItem
                text={t(
                  "login.features.anywhere",
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
          <div className="w-full max-w-md">
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
                    "login.welcomeBack",
                  )}
                </p>

                <h2 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
                  {t(
                    "login.pageTitle",
                  )}
                </h2>

                <p className="mt-3 text-sm leading-6 text-slate-500">
                  {t(
                    "login.pageSubtitle",
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
                <div className="space-y-2">
                  <Label htmlFor="login">
                    {t(
                      "login.username",
                    )}
                  </Label>

                  <div className="relative">
                    <UserRound className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

                    <Input
                      id="login"
                      name="login"
                      type="text"
                      value={
                        loginValue
                      }
                      onChange={(
                        event,
                      ) => {
                        setLoginValue(
                          event.target
                            .value,
                        );

                        setError("");
                      }}
                      placeholder={t(
                        "login.usernamePlaceholder",
                      )}
                      autoComplete="username"
                      autoCapitalize="none"
                      spellCheck={false}
                      disabled={
                        isLoading
                      }
                      required
                      className="h-11 ps-10"
                      dir="ltr"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-4">
                    <Label htmlFor="password">
                      {t(
                        "login.password",
                      )}
                    </Label>


                  </div>

                  <div className="relative">
                    <LockKeyhole className="pointer-events-none absolute start-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" />

                    <Input
                      id="password"
                      name="password"
                      type={
                        showPassword
                          ? "text"
                          : "password"
                      }
                      value={
                        password
                      }
                      onChange={(
                        event,
                      ) => {
                        setPassword(
                          event.target
                            .value,
                        );

                        setError("");
                      }}
                      placeholder={t(
                        "login.passwordPlaceholder",
                      )}
                      autoComplete="current-password"
                      disabled={
                        isLoading
                      }
                      required
                      className="h-11 ps-10 pe-10"
                    />

                    <button
                      type="button"
                      onClick={() =>
                        setShowPassword(
                          (current) =>
                            !current,
                        )
                      }
                      disabled={
                        isLoading
                      }
                      aria-label={
                        showPassword
                          ? t(
                              "login.hidePassword",
                            )
                          : t(
                              "login.showPassword",
                            )
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

                <label className="flex cursor-pointer items-center gap-3 text-sm text-slate-600">
                  <input
                    type="checkbox"
                    checked={
                      rememberMe
                    }
                    onChange={(
                      event,
                    ) =>
                      setRememberMe(
                        event.target
                          .checked,
                      )
                    }
                    disabled={
                      isLoading
                    }
                    className="size-4 rounded border-slate-300 accent-blue-600"
                  />

                  {t(
                    "login.rememberMe",
                  )}
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
                        "login.signingIn",
                      )}
                    </>
                  ) : (
                    t(
                      "login.signIn",
                    )
                  )}
                </Button>
              </form>

              <div className="my-7 flex items-center gap-4">
                <div className="h-px flex-1 bg-slate-200" />

                <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
                  {t(
                    "login.newToPrimeERP",
                  )}
                </span>

                <div className="h-px flex-1 bg-slate-200" />
              </div>

              <p className="text-center text-sm text-slate-600">
                {t(
                  "login.noAccount",
                )}{" "}
                <Link
                  to="/register"
                  className="font-semibold text-blue-600 transition-colors hover:text-blue-700 hover:underline"
                >
                  {t(
                    "login.startTrial",
                  )}
                </Link>
              </p>
            </div>

            <p className="mt-6 text-center text-xs text-slate-400">
              {t(
                "common.secured",
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

