import type { AxiosError } from "axios";

export function getApiErrorMessage(error: AxiosError): string {
  const data = error.response?.data as
    | {
        detail?: string;
        message?: string;
      }
    | undefined;

  return (
    data?.detail ??
    data?.message ??
    error.message ??
    "Unexpected server error."
  );
}