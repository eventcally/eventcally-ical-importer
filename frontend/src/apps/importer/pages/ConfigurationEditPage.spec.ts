import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const GET = vi.fn();
const POST = vi.fn();
const PUT = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
    PUT: (...a: unknown[]) => PUT(...a),
  },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import { takeFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import ConfigurationEditPage from "./ConfigurationEditPage.vue";

const values = {
  title: "Sitzungen",
  identifier_tag: "tag-1",
  url: "https://example.com/feed.ics",
  name: '{{ standard["name"] }}',
  organizer_name: "",
  place_name: "",
  start: "",
  description: "",
  end: "",
  allday: "",
  external_link: "",
  tags: "",
  categories: "",
  photo_url: "",
  photo_copyright_text: "",
};

const form = {
  data: {
    id: 3,
    organization_name: "Goslar",
    values,
    mapper_fields: ["name", "organizer_name", "place_name", "start"],
  },
};

beforeEach(() => {
  [GET, POST, PUT, success].forEach((f) => f.mockReset());
  document.body.innerHTML = "";
  sessionStorage.clear();
  // a fresh copy: the page keeps (and updates) what it loaded
  GET.mockImplementation(async () => structuredClone(form));
});

const mountIt = () => mountPage(ConfigurationEditPage, { id: 3 }, "/configurations/3/update");

describe("ConfigurationEditPage", () => {
  it("fills the form with the stored values", async () => {
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith("/bff/configurations/{id}/form", {
      params: { path: { id: 3 } },
    });
    expect(wrapper.find("h1").text()).toBe("Update Sitzungen");
    expect((wrapper.find("#title").element as HTMLInputElement).value).toBe("Sitzungen");
    expect(wrapper.find("#url").attributes("type")).toBe("url");
    expect((wrapper.find("#name").element as HTMLTextAreaElement).value).toBe(
      '{{ standard["name"] }}',
    );
    // the mapper fields in the server's order, labelled with their names
    expect(wrapper.findAll("textarea").map((e) => e.attributes("id"))).toEqual(
      form.data.mapper_fields,
    );
    expect(wrapper.find('label[for="organizer_name"]').text()).toBe("organizer_name");
  });

  it("saves the edited values and stays on the page", async () => {
    PUT.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountIt();

    await wrapper.find("#organizer_name").setValue("Stadt Goslar");
    await wrapper.find("#form").trigger("submit");
    await flushPromises();

    expect(PUT).toHaveBeenCalledWith("/bff/configurations/{id}", {
      params: { path: { id: 3 } },
      body: { ...values, organizer_name: "Stadt Goslar" },
    });
    expect(success).toHaveBeenCalledWith("Configuration saved");
    expect(router.currentRoute.value.fullPath).toBe("/configurations/3/update");
  });

  it("shows the field errors of a 422", async () => {
    PUT.mockResolvedValue({
      response: { ok: false },
      error: {
        name: "Unprocessable Entity",
        message: "Invalid",
        errors: [{ loc: ["identifier_tag"], msg: "String should have at least 1 character" }],
      },
    });
    const { wrapper } = await mountIt();

    await wrapper.find("#identifier_tag").setValue("");
    await wrapper.find("#form").trigger("submit");
    await flushPromises();

    expect(wrapper.find("#identifier_tag").classes()).toContain("is-invalid");
    expect(wrapper.find(".invalid-feedback").text()).toContain("at least 1 character");
    expect(wrapper.find('[data-test="error"]').text()).toBe("Invalid");
    expect(success).not.toHaveBeenCalled();
  });

  it("previews the unsaved values", async () => {
    POST.mockResolvedValue({
      data: {
        status: "failure",
        log_entries: [
          {
            type: "vevent",
            message: "Event importiert",
            context: {
              vevent: "BEGIN:VEVENT",
              standard: { name: "Sitzung" },
              event: { name: "<b>Sitzung</b>" },
              errors: [],
              hints: [{ key: "start", msg: "Required start is missing" }],
            },
          },
          { type: null, message: "Error loading url", context: null },
        ],
      },
    });
    const { wrapper } = await mountIt();

    expect(wrapper.find('[data-test="preview-table"]').exists()).toBe(false);
    await wrapper.find("#name").setValue("x");
    await wrapper.find('[data-test="preview"]').trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/configurations/{id}/preview", {
      params: { path: { id: 3 } },
      body: { ...values, name: "x" },
    });
    const rows = wrapper.findAll('[data-test="preview-table"] tbody tr');
    expect(rows).toHaveLength(2);
    const cells = rows[0].findAll("td");
    expect(cells[0].text()).toBe("BEGIN:VEVENT");
    expect(cells[1].text()).toContain('"name": "Sitzung"');
    // rendered as text, never as markup
    expect(cells[2].find("b").exists()).toBe(false);
    expect(cells[2].text()).toContain("<b>Sitzung</b>");
    expect(cells[3].text()).toBe("");
    expect(wrapper.find('[data-test="preview-table"] [data-test="status"]').text()).toBe("failure");
    expect(cells[4].text()).toContain("Required start is missing");
    expect(rows[1].find("td").attributes("colspan")).toBe("5");
    expect(rows[1].text()).toBe("Error loading url");
  });

  it("deletes after confirming and leaves a message for the list", async () => {
    POST.mockResolvedValue({ response: { ok: true } });
    const { wrapper, router } = await mountIt();

    await wrapper.find('[data-test="delete"]').trigger("click");
    await flushPromises();
    expect(POST).not.toHaveBeenCalled();

    const confirm = document.body.querySelector<HTMLButtonElement>(".modal .btn-danger")!;
    expect(document.body.querySelector(".modal")!.textContent).toContain("Delete configuration?");
    confirm.click();
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/configurations/{id}/delete", {
      params: { path: { id: 3 } },
    });
    expect(router.currentRoute.value.fullPath).toBe("/configurations");
    expect(takeFlash()).toBe("Configuration deleted");
  });

  it("closes to the configuration page", async () => {
    const { wrapper, router } = await mountIt();

    await wrapper.find('[data-test="close"]').trigger("click");
    await flushPromises();

    expect(router.currentRoute.value.fullPath).toBe("/configurations/3");
  });
});
