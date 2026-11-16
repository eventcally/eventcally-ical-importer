import { describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));
vi.mock("@/shared/api", () => ({ api: {} }));

import { router } from "./router";

describe("router", () => {
  it("resolves the page URLs of the Flask shells", () => {
    expect(router.resolve("/configurations").name).toBe("configurations");
    expect(router.resolve("/configurations/3").name).toBe("configuration");
    expect(router.resolve("/configurations/3/update").name).toBe("configuration-update");
    expect(router.resolve("/configurations/3/runs/8").name).toBe("run");
  });

  it("falls back to the not-found page", () => {
    expect(router.resolve("/configurations/abc").name).toBe("not-found");
  });
});
