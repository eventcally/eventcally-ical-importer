import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import JsonDetails from "./JsonDetails.vue";

describe("JsonDetails", () => {
  it("folds indented JSON behind the label", () => {
    const wrapper = mount(JsonDetails, { props: { value: { a: 1 }, label: "Data" } });

    expect(wrapper.find("summary").text()).toBe("Data");
    expect(wrapper.find("pre").text()).toBe('{\n  "a": 1\n}');
    expect(wrapper.find("details").attributes("open")).toBeUndefined();
  });

  it("shows a string as is and nothing for null", () => {
    expect(
      mount(JsonDetails, { props: { value: "BEGIN:VEVENT", label: "x", open: true } })
        .find("pre")
        .text(),
    ).toBe("BEGIN:VEVENT");
    expect(mount(JsonDetails, { props: { value: null, label: "x" } }).find("details").exists()).toBe(
      false,
    );
  });
});
