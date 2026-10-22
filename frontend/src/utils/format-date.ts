import { useEffect, useState } from "react";

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
    const refresh = () => setFormat(getCompanyDateFormat(companyId));
    window.addEventListener(FORMAT_CHANGED_EVENT, refresh);
    window.addEventListener("storage", refresh);
    return () => {
      window.removeEventListener(FORMAT_CHANGED_EVENT, refresh);
      window.removeEventListener("storage", refresh);
    };
  }, [companyId]);
  return format;
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
