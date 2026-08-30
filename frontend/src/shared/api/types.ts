import type { AxiosError, AxiosResponse } from "axios";

export type AxiosApiResponse<T> = AxiosResponse<T>;

export type ApiError = AxiosError<{
  detail?: string;
  message?: string;
  errors?: unknown;
}>;

export interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}