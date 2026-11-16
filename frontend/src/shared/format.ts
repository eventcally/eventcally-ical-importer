// The server-rendered pages showed times in Europe/Berlin (BABEL_DEFAULT_TIMEZONE).
const TIME_ZONE = "Europe/Berlin";

export function formatDateTime(iso: string | null | undefined, locale: string): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "medium",
    timeZone: TIME_ZONE,
  }).format(new Date(iso));
}

/** Indented JSON for the read-only data boxes; empty for null. */
export function formatJson(value: unknown): string {
  if (value === null || value === undefined) return "";
  return JSON.stringify(value, null, 2);
}
