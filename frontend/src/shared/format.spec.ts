import { describe, expect, it } from "vitest";
import { formatDateTime, formatJson } from "./format";

describe("formatDateTime", () => {
  it("shows UTC times in Europe/Berlin", () => {
    expect(formatDateTime("2026-01-17T16:00:00Z", "de")).toBe("17.01.2026, 17:00:00");
    expect(formatDateTime(null, "de")).toBe("");
  });
});

describe("formatJson", () => {
  it("indents and treats null as empty", () => {
    expect(formatJson({ a: 1 })).toBe('{\n  "a": 1\n}');
    expect(formatJson(null)).toBe("");
  });
});
