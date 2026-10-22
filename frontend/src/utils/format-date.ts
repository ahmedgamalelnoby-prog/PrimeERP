import { useEffect, useState } from "react";
import client from "@/shared/api/client";

export type CompanyDateFormat = "DD/MM/YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";

const ALLOWED_FORMATS: readonly CompanyDateFormat[] = [
  "DD/MM/YYYY",
  "MM/DD/YYYY",
  "YYYY-MM-DD",
];

const DEFAULT_FORMAT: CompanyDateFormat = "DD/MM/YYYY";
const COMPANY_DATE_FORMAT_PREFIX = "primeerp_company_date_format:";
const FORMAT_CHANGED_EVENT = "primeerp:company-date-format-changed";

/** Return today in the browser local timezone for date-input values. */
export function getLocalISODate(now: Date = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function setCompanyDateFormat(companyId: number, value: unknown): void {
  if (!Number.isInteger(companyId) || companyId <= 0 || !isCompanyDateFormat(value)) return;
  try {
    localStorage.setItem(`${COMPANY_DATE_FORMAT_PREFIX}${companyId}`, value);
    window.dispatchEvent(new Event(FORMAT_CHANGED_EVENT));
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
}

export function useCompanyDateFormat(companyId?: number | null): CompanyDateFormat {
  const [format, setFormat] = useState(() => getCompanyDateFormat(companyId));
  useEffect(() => {
    let active = true;
    const refresh = () => setFormat(getCompanyDateFormat(companyId));
    window.addEventListener(FORMAT_CHANGED_EVENT, refresh);
    window.addEventListener("storage", refresh);

    let selectedId = companyId ?? null;
    if (selectedId == null) {
      try {
        const raw = Number(localStorage.getItem("company_id"));
        selectedId = Number.isSafeInteger(raw) && raw > 0 ? raw : null;
      } catch {
        selectedId = null;
      }
    }
    if (selectedId && Number.isSafeInteger(selectedId) && selectedId > 0) {
      void client.get<{ company_id: number; date_format: unknown }>(
        "/company-settings/date-format",
        { params: { company_id: selectedId } },
      ).then(({ data }) => {
        if (!active || data.company_id !== selectedId || !isCompanyDateFormat(data.date_format)) return;
        setCompanyDateFormat(selectedId as number, data.date_format);
        setFormat(data.date_format);
      }).catch(() => {
        // Keep the last validated cached preference if the server is temporarily unavailable.
      });
    }

    return () => {
      active = false;
      window.removeEventListener(FORMAT_CHANGED_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [companyId]);
  return format;
}

/** Fetch the selected company's calendar date from the backend clock.
 * Returns an empty string when the company or authoritative clock is unavailable;
 * callers should not silently substitute the workstation clock for accounting dates.
 */
export function useCompanyToday(companyId?: number | null): string {
  const [today, setToday] = useState("");
  useEffect(() => {
    let active = true;
    setToday("");
    if (!Number.isSafeInteger(companyId) || !companyId || companyId <= 0) {
      return () => { active = false; };
    }
    void client.get<{ company_id: number; company_date: string }>(
      "/company-settings/clock",
      { params: { company_id: companyId } },
    ).then(({ data }) => {
      if (!active || data.company_id !== companyId || !/^\d{4}-\d{2}-\d{2}$/.test(data.company_date)) return;
      const [year, month, day] = data.company_date.split("-").map(Number);
      const valid = new Date(Date.UTC(year, month - 1, day));
      if (valid.getUTCFullYear() !== year || valid.getUTCMonth() !== month - 1 || valid.getUTCDate() !== day) return;
      setToday(data.company_date);
    }).catch(() => {
      // No workstation-clock fallback: the form remains without an implicit date.
    });
    return () => { active = false; };
  }, [companyId]);
  return today;
}

export function getCompanyDateFormat(companyId?: number | null): CompanyDateFormat {
  try {
    // Access itself can throw in restricted browser contexts, so keep every
    // storage read inside the guard (not only the company-specific lookup).
    if (typeof localStorage === "undefined") return DEFAULT_FORMAT;
    const selectedId = companyId ?? Number(localStorage.getItem("company_id"));
    if (!Number.isInteger(selectedId) || selectedId <= 0) return DEFAULT_FORMAT;
    const saved = localStorage.getItem(`${COMPANY_DATE_FORMAT_PREFIX}${selectedId}`);
    return isCompanyDateFormat(saved) ? saved : DEFAULT_FORMAT;
  } catch {
    return DEFAULT_FORMAT;
  }
}

/** Format ISO calendar dates without timezone conversion or changing timestamp values. */
export function formatCompanyDate(value: string, format: CompanyDateFormat = getCompanyDateFormat()): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})(?=$|T|\s)(.*)$/.exec(value);
  if (!match) return value;

  const [, year, month, day, suffix] = match;
  const yearNumber = Number(year);
  const monthNumber = Number(month);
  const dayNumber = Number(day);
  const daysInMonth = monthNumber >= 1 && monthNumber <= 12
    ? new Date(Date.UTC(yearNumber, monthNumber, 0)).getUTCDate()
    : 0;

  // Avoid presenting malformed ISO-like strings as valid dates.
  if (dayNumber < 1 || dayNumber > daysInMonth) return value;

  let formatted: string;
  if (format === "MM/DD/YYYY") formatted = `${month}/${day}/${year}`;
  else if (format === "YYYY-MM-DD") formatted = `${year}-${month}-${day}`;
  else formatted = `${day}/${month}/${year}`;

  return `${formatted}${suffix}`;
}

export function isCompanyDateFormat(value: unknown): value is CompanyDateFormat {
  return typeof value === "string" && ALLOWED_FORMATS.includes(value as CompanyDateFormat);
}


export type CompanyClockDateState = {
  companyDate: string;
  loading: boolean;
  error: string;
};

/**
 * Resolve date-only defaults from the authenticated backend clock and the
 * selected company's timezone. Never silently fall back to the device clock:
 * if the server clock cannot be reached, the caller receives an empty date.
 */
export function useCompanyClockDate(companyId?: number | null): CompanyClockDateState {
  const [state, setState] = useState<CompanyClockDateState>({
    companyDate: "",
    loading: true,
    error: "",
  });

  useEffect(() => {
    let active = true;
    const load = async () => {
      let selectedId = companyId ?? null;
      if (selectedId == null) {
        try {
          const raw = Number(localStorage.getItem("company_id"));
          selectedId = Number.isInteger(raw) && raw > 0 ? raw : null;
        } catch {
          selectedId = null;
        }
      }
      if (!selectedId || !Number.isInteger(selectedId) || selectedId <= 0) {
        if (active) setState({ companyDate: "", loading: false, error: "اختر شركة فعالة أولاً." });
        return;
      }
      if (active) setState({ companyDate: "", loading: true, error: "" });
      try {
        const response = await client.get<{ company_id: number; company_date: string }>(
          "/company-settings/clock",
          { params: { company_id: selectedId } },
        );
        const date = response.data?.company_date;
        if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date)) {
          throw new Error("استجابة ساعة الشركة غير صالحة.");
        }
        if (active) setState({ companyDate: date, loading: false, error: "" });
      } catch (error) {
        const message = (error as { response?: { data?: { detail?: string } }; message?: string })
          ?.response?.data?.detail || (error as { message?: string })?.message || "تعذر جلب تاريخ الشركة من الخادم.";
        if (active) setState({ companyDate: "", loading: false, error: message });
      }
    };
    void load();
    return () => { active = false; };
  }, [companyId]);

  return state;
}
