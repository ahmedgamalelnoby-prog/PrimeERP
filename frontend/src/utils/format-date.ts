export type CompanyDateFormat = "DD/MM/YYYY" | "MM/DD/YYYY" | "YYYY-MM-DD";

const ALLOWED_FORMATS: readonly CompanyDateFormat[] = [
  "DD/MM/YYYY",
  "MM/DD/YYYY",
  "YYYY-MM-DD",
];

/** Format ISO calendar dates without timezone conversion or changing timestamp values. */
export function formatCompanyDate(value: string, format: CompanyDateFormat): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  if (!match) return value;

  const [, year, month, day] = match;
  if (format === "MM/DD/YYYY") return `${month}/${day}/${year}`;
  if (format === "YYYY-MM-DD") return `${year}-${month}-${day}`;
  return `${day}/${month}/${year}`;
}

export function isCompanyDateFormat(value: unknown): value is CompanyDateFormat {
  return typeof value === "string" && ALLOWED_FORMATS.includes(value as CompanyDateFormat);
}
