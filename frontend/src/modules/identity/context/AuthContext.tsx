import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authService } from "../services/authentication.service";
import client from "../../../shared/api/client";
import i18n from "../../../shared/i18n/i18n";
import { storage } from "../../../shared/utils/storage";
import { setCompanyDateFormat } from "../../../utils/format-date";

import type { AuthenticatedUser } from "../types/user";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (
    usernameOrEmail: string,
    password: string,
    tenantSlug?: string | null,
    tenantName?: string | null,
  ) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext =
  createContext<AuthContextValue | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = async (): Promise<void> => {
    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch (error) {
      console.error("Unable to refresh authenticated user:", error);
      void authService.logout();
      setUser(null);
    }
  };

  useEffect(() => {
    // Platform administrators must explicitly select a tenant before any
    // tenant-scoped company settings request is made.
    if (!user || user.is_platform_admin || user.tenant_id === null) return;

    let cancelled = false;
    const applyCompanyLanguage = async (): Promise<void> => {
      try {
        const { data: companies } = await client.get<Array<{ id: number }>>(
          "/companies?active_only=true",
        );
        if (cancelled || companies.length === 0) return;

        const storedCompanyId = Number(localStorage.getItem("company_id")) || 0;
        const companyExists = companies.some(
          (company) => company.id === storedCompanyId,
        );
        const companyId = companyExists ? storedCompanyId : companies[0].id;

        if (!companyExists) {
          localStorage.setItem("company_id", String(companyId));
        }

        const { data: settings } = await client.get<{
          settings: Array<{ key: string; value: unknown }>;
        }>("/company-settings", { params: { company_id: companyId } });
        if (cancelled) return;

        const dateFormat = settings.settings.find(
          (setting) => setting.key === "general.date_format",
        )?.value;
        setCompanyDateFormat(companyId, dateFormat);

        const language = settings.settings.find(
          (setting) => setting.key === "general.default_language",
        )?.value;
        if (language === "ar" || language === "en") {
          await i18n.changeLanguage(language);
        }
      } catch {
        // Company settings are optional during bootstrap.
      }
    };

    void applyCompanyLanguage();
    return () => {
      cancelled = true;
    };
  }, [user]);

  useEffect(() => {
    const initializeAuthentication = async (): Promise<void> => {
      if (!storage.getAccessToken()) {
        setIsLoading(false);
        return;
      }

      try {
        await refreshUser();
      } finally {
        setIsLoading(false);
      }
    };

    void initializeAuthentication();
  }, []);

  const login = async (
    usernameOrEmail: string,
    password: string,
    tenantSlug: string | null = null,
    tenantName: string | null = null,
  ): Promise<void> => {
    const response = await authService.login({
      login: usernameOrEmail.trim(),
      password,
      tenant_slug: tenantSlug?.trim() || null,
      tenant_name: tenantName?.trim() || null,
    });

    setUser(response.user);
  };

  const logout = (): void => {
    void authService.logout();
    setUser(null);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: Boolean(user),
      login,
      logout,
      refreshUser,
    }),
    [user, isLoading],
  );

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }

  return context;
}
