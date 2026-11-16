import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import StatusBadge from "./StatusBadge.vue";

describe("StatusBadge", () => {
  it("colors success and failure", () => {
    expect(mount(StatusBadge, { props: { status: "success" } }).classes()).toContain(
      "text-bg-success",
    );
    const failure = mount(StatusBadge, { props: { status: "failure" } });
    expect(failure.classes()).toContain("text-bg-danger");
    expect(failure.text()).toBe("failure");
  });

  it("shows an unknown status neutrally and nothing without one", () => {
    expect(mount(StatusBadge, { props: { status: "running" } }).classes()).toContain(
      "text-bg-secondary",
    );
    expect(mount(StatusBadge, { props: { status: null } }).find("span").exists()).toBe(false);
  });
});
