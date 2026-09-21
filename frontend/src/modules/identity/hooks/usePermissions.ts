import { useCallback } from "react";

import { useAuth } from "../context/AuthContext";

export function usePermissions() {
  const { user } = useAuth();

  const hasPermission = useCallback(
    (permission: string) =>
      Boolean(
        user?.is_platform_admin ||
          user?.is_superuser ||
          user?.permissions?.includes("*") ||
          user?.permissions?.includes(permission),
      ),
    [user],
  );

  const hasModule = useCallback(
    (moduleCode: string) =>
      Boolean(
        user?.is_platform_admin ||
          user?.is_superuser ||
          user?.enabled_modules?.includes(moduleCode),
      ),
    [user],
  );

  const hasResourceAccess = useCallback(
    (resource: string) =>
      Boolean(
        user?.is_platform_admin ||
          user?.is_superuser ||
          user?.permissions?.includes("*") ||
          user?.permissions?.some((code) => code === resource || code.startsWith(`${resource}.`)),
      ),
    [user],
  );

  return { hasPermission, hasModule, hasResourceAccess };
}
