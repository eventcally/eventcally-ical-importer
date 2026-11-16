interface FieldErrorItem {
  loc: string[];
  msg: string;
}

/** The `message` of an error answer, or the fallback (network errors have none). */
export function errorMessage(error: unknown, fallback: string): string {
  const message = (error as { message?: string } | undefined)?.message;
  return message || fallback;
}

/** The field errors of a 422 answer by field name; null for other errors. */
export function fieldErrors(error: unknown): Record<string, string> | null {
  if (!error || typeof error !== "object" || !("errors" in error)) return null;
  const result: Record<string, string> = {};
  for (const item of (error as { errors: FieldErrorItem[] }).errors) {
    const key = item.loc[item.loc.length - 1] ?? "";
    if (!(key in result)) result[key] = item.msg;
  }
  return result;
}
