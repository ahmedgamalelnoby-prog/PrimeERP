import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";
import type { AxiosError } from "axios";
import { toast } from "react-hot-toast";
import { useTranslation } from "react-i18next";

import { getApiErrorMessage } from "@/shared/api/errors";
import { useDebounce } from "@/shared/hooks/useDebounce";

import { rolesService } from "../services/roles.service";

import type { Permission } from "../types/permission";
import type {
  Role,
  RoleCreatePayload,
  RolesFilters,
  RoleUpdatePayload,
} from "../types/role";

export function useRoles() {
  const { t } = useTranslation();
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] =
    useState<Permission[]>([]);

  const [loading, setLoading] = useState(true);
  const [permissionsLoading, setPermissionsLoading] =
    useState(true);

  const [processingId, setProcessingId] =
    useState<number | null>(null);

  const [isCreating, setIsCreating] =
    useState(false);

  const [filters, setFilters] =
    useState<RolesFilters>({
      search: "",
    });

  const debouncedSearch = useDebounce(
    filters.search ?? "",
    400,
  );

  const effectiveFilters = useMemo<RolesFilters>(
    () => ({
      ...filters,
      search: debouncedSearch,
    }),
    [filters, debouncedSearch],
  );

  const showError = useCallback((error: unknown) => {
    console.error("Roles operation error:", error);

    toast.error(
      getApiErrorMessage(error as AxiosError),
    );
  }, []);

  const loadRoles = useCallback(async () => {
    try {
      setLoading(true);

      const data =
        await rolesService.getRoles(
          effectiveFilters,
        );

      setRoles(data);
    } catch (error) {
      showError(error);
    } finally {
      setLoading(false);
    }
  }, [effectiveFilters, showError]);

  const loadPermissions = useCallback(async () => {
    try {
      setPermissionsLoading(true);

      const data =
        await rolesService.getPermissions();

      setPermissions(
        data.filter(
          (permission) => permission.is_active,
        ),
      );
    } catch (error) {
      showError(error);
    } finally {
      setPermissionsLoading(false);
    }
  }, [showError]);

  useEffect(() => {
    void loadRoles();
  }, [loadRoles]);

  useEffect(() => {
    void loadPermissions();
  }, [loadPermissions]);

  const createRole = async (
    payload: RoleCreatePayload,
  ): Promise<boolean> => {
    try {
      setIsCreating(true);

      await rolesService.createRole(payload);

      toast.success(t("roles.notifications.created"));

      await loadRoles();

      return true;
    } catch (error) {
      showError(error);
      return false;
    } finally {
      setIsCreating(false);
    }
  };

  const updateRole = async (
    id: number,
    payload: RoleUpdatePayload,
  ): Promise<boolean> => {
    try {
      setProcessingId(id);

      await rolesService.updateRole(
        id,
        payload,
      );

      toast.success(t("roles.notifications.updated"));

      await loadRoles();

      return true;
    } catch (error) {
      showError(error);
      return false;
    } finally {
      setProcessingId(null);
    }
  };

  const updatePermissions = async (
    id: number,
    permissionIds: number[],
  ): Promise<boolean> => {
    try {
      setProcessingId(id);

      await rolesService.updatePermissions(
        id,
        permissionIds,
      );

      toast.success(
        t("roles.notifications.permissionsUpdated"),
      );

      await loadRoles();

      return true;
    } catch (error) {
      showError(error);
      return false;
    } finally {
      setProcessingId(null);
    }
  };

  const toggleStatus = async (
    role: Role,
  ): Promise<boolean> => {
    try {
      setProcessingId(role.id);

      await rolesService.changeStatus(
        role.id,
        {
          is_active: !role.is_active,
        },
      );

      toast.success(
        role.is_active
          ? t("roles.notifications.deactivated")
          : t("roles.notifications.activated"),
      );

      await loadRoles();

      return true;
    } catch (error) {
      showError(error);
      return false;
    } finally {
      setProcessingId(null);
    }
  };

  const deleteRole = async (
    role: Role,
  ): Promise<boolean> => {
    if (role.users_count > 0) {
      toast.error(
        t("roles.notifications.deleteAssigned"),
      );

      return false;
    }

    try {
      setProcessingId(role.id);

      await rolesService.deleteRole(role.id);

      toast.success(t("roles.notifications.deleted"));

      await loadRoles();

      return true;
    } catch (error) {
      showError(error);
      return false;
    } finally {
      setProcessingId(null);
    }
  };

  return {
    roles,
    permissions,

    loading,
    permissionsLoading,
    isCreating,
    processingId,

    filters,
    setFilters,

    reloadRoles: loadRoles,
    reloadPermissions: loadPermissions,

    createRole,
    updateRole,
    updatePermissions,
    toggleStatus,
    deleteRole,
  };
}