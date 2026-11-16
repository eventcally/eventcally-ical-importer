import { describe, expect, it } from "vitest";
import { errorMessage, fieldErrors } from "./apiError";

describe("errorMessage", () => {
  it("prefers the server message", () => {
    expect(errorMessage({ message: "Nope" }, "Error")).toBe("Nope");
    expect(errorMessage(undefined, "Error")).toBe("Error");
  });
});

describe("fieldErrors", () => {
  it("maps a 422 answer by field name, first message wins", () => {
    const error = {
      name: "Unprocessable Entity",
      message: "x",
      errors: [
        { loc: ["identifier_tag"], msg: "too short" },
        { loc: ["identifier_tag"], msg: "other" },
        { loc: ["title"], msg: "too long" },
      ],
    };

    expect(fieldErrors(error)).toEqual({ identifier_tag: "too short", title: "too long" });
  });

  it("is null for other errors", () => {
    expect(fieldErrors({ name: "Not Found", message: "x" })).toBeNull();
    expect(fieldErrors(undefined)).toBeNull();
  });
});
