import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { authService } from "../services/authentication.service";
import { storage } from "../../../shared/utils/storage";

import type { AuthenticatedUser } from "../types/user";

interface AuthContextValue {
  user: AuthenticatedUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (
    usernameOrEmail: string,
    password: string,
    tenantSlug?: string | null,
  ) => Promise<void>;

  logout: () => void;
  refreshUser: () => Promise<void>;
}

export const AuthContext =
  createContext<AuthContextValue | undefined>(
    undefined,
  );

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [user, setUser] =
    useState<AuthenticatedUser | null>(null);

  const [isLoading, setIsLoading] =
    useState(true);

  const refreshUser =
    async (): Promise<void> => {
      try {
        const currentUser =
          await authService.getCurrentUser();

        setUser(currentUser);
      } catch (error) {
        console.error(
          "Unable to refresh authenticated user:",
          error,
        );

        authService.logout();
        setUser(null);
      }
    };

  useEffect(() => {
    const initializeAuthentication =
      async (): Promise<void> => {
        const token =
          storage.getAccessToken();

        if (!token) {
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
  ): Promise<void> => {
    const normalizedLogin =
      usernameOrEmail.trim();

    const response =
      await authService.login({
        login: normalizedLogin,
        password,
        tenant_slug:
          tenantSlug?.trim() || null,
      });

    setUser(response.user);
  };

  const logout = (): void => {
    authService.logout();
    setUser(null);
  };

  const value =
    useMemo<AuthContextValue>(
      () => ({
        user,
        isLoading,
        isAuthenticated:
          Boolean(user),
        login,
        logout,
        refreshUser,
      }),
      [user, isLoading],
    );

  return (
    <AuthContext.Provider
      value={value}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context =
    useContext(AuthContext);

  if (!context) {
    throw new Error(
      "useAuth must be used inside AuthProvider",
    );
  }

  return context;
}