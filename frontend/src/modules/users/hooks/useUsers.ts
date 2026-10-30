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

import { usersService } from "../services/users.service";

import type {
  PageMeta,
  User,
  UserCreatePayload,
  UsersFilters,
  UserUpdatePayload,
} from "../types/user";

const initialMeta: PageMeta = {
  page: 1,
  page_size: 25,
  total: 0,
  total_pages: 0,
  has_next: false,
  has_previous: false,
};

export function useUsers() {
  const { t } = useTranslation();
  const [users, setUsers] = useState<User[]>([]);
  const [meta, setMeta] =
    useState<PageMeta>(initialMeta);

  const [loading, setLoading] = useState(true);

  const [processingId, setProcessingId] =
    useState<number | null>(null);

  const [filters, setFilters] =
    useState<UsersFilters>({
      search: "",
      page: 1,
      page_size: 25,
    });

  const debouncedSearch = useDebounce(
    filters.search,
    400,
  );

  const effectiveFilters = useMemo(
    () => ({
      ...filters,
      search: debouncedSearch,
    }),
    [filters, debouncedSearch],
  );

  const loadUsers = useCallback(async () => {
    try {
      setLoading(true);

      const data = await usersService.getAll(
        effectiveFilters,
      );

      setUsers(data.items);
      setMeta(data.meta);
    } catch (error) {
      console.error(
        "Failed to load users:",
        error,
      );

      toast.error(
        getApiErrorMessage(
          error as AxiosError,
        ),
      );

      setUsers([]);
      setMeta(initialMeta);
    } finally {
      setLoading(false);
    }
  }, [effectiveFilters]);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  const createUser = async (
    payload: UserCreatePayload,
  ) => {
    try {
      await usersService.create(payload);

      toast.success(
        t("users.notifications.created"),
      );

      await loadUsers();

      return true;
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error as AxiosError,
        ),
      );

      return false;
    }
  };

  const updateUser = async (
    id: number,
    payload: UserUpdatePayload,
  ) => {
    try {
      setProcessingId(id);

      await usersService.update(id, payload);

      toast.success(
        t("users.notifications.updated"),
      );

      await loadUsers();

      return true;
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error as AxiosError,
        ),
      );

      return false;
    } finally {
      setProcessingId(null);
    }
  };

  const toggleStatus = async (
    user: User,
  ) => {
    try {
      setProcessingId(user.id);

      await usersService.changeStatus(
        user.id,
        {
          is_active: !user.is_active,
        },
      );

      toast.success(
        user.is_active
          ? t("users.notifications.deactivated")
          : t("users.notifications.activated"),
      );

      await loadUsers();
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error as AxiosError,
        ),
      );
    } finally {
      setProcessingId(null);
    }
  };

  const deleteUser = async (
    user: User,
  ) => {
    try {
      setProcessingId(user.id);

      await usersService.remove(user.id);

      toast.success(
        t("users.notifications.deleted"),
      );

      await loadUsers();

      return true;
    } catch (error) {
      toast.error(
        getApiErrorMessage(
          error as AxiosError,
        ),
      );

      return false;
    } finally {
      setProcessingId(null);
    }
  };

  const goToPage = (page: number) => {
    setFilters((current) => ({
      ...current,
      page,
    }));
  };

  const changePageSize = (
    pageSize: number,
  ) => {
    setFilters((current) => ({
      ...current,
      page: 1,
      page_size: pageSize,
    }));
  };

  return {
    users,
    meta,
    loading,
    processingId,
    filters,

    setFilters,
    reload: loadUsers,
    goToPage,
    changePageSize,

    createUser,
    updateUser,
    toggleStatus,
    deleteUser,
  };
}