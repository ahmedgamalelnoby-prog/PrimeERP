export type CompanyDateFormat = "DD/MM/YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";

const ALLOWED_FORMATS: readonly CompanyDateFormat[] = [
  "DD/MM/YYYY",
  "MM/DD/YYYY",
  "YYYY-MM-DD",
];

const DEFAULT_FORMAT: CompanyDateFormat = "DD/MM/YYYY";
const COMPANY_DATE_FORMAT_PREFIX = "primeerp_company_date_format:";

export function setCompanyDateFormat(companyId: number, value: unknown): void {
  if (!Number.isInteger(companyId) || companyId <= 0 || !isCompanyDateFormat(value)) return;
  try {
    localStorage.setItem(`${COMPANY_DATE_FORMAT_PREFIX}${companyId}`, value);
  } catch {
    // Storage can be unavailable in private or restricted browser contexts.
  }
}

export function getCompanyDateFormat(companyId?: number | null): CompanyDateFormat {
  if (typeof localStorage === "undefined") return DEFAULT_FORMAT;
  const selectedId = companyId ?? Number(localStorage.getItem("company_id"));
  if (!Number.isInteger(selectedId) || selectedId <= 0) return DEFAULT_FORMAT;
  try {
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
