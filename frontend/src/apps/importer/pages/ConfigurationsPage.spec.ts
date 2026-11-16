import { flushPromises } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
  },
}));
const success = vi.hoisted(() => vi.fn());
vi.mock("@/shared/notify", () => ({
  useNotify: () => ({ success, error: vi.fn() }),
}));

import { setFlash } from "@/shared/flash";
import { mountPage } from "../testing";
import ConfigurationsPage from "./ConfigurationsPage.vue";

const list = {
  data: {
    configurations: [
      { id: 3, title: "Sitzungen", organization_name: "Goslar" },
      { id: 4, title: null, organization_name: "Goslar" },
    ],
    app_installations: [{ id: 9, organization_name: "Goslar" }],
  },
};

beforeEach(() => {
  [GET, POST, success].forEach((f) => f.mockReset());
  document.body.innerHTML = "";
  sessionStorage.clear();
});

describe("ConfigurationsPage", () => {
  it("lists the configurations and the organizations", async () => {
    GET.mockResolvedValue(list);
    const { wrapper } = await mountPage(ConfigurationsPage);

    expect(GET).toHaveBeenCalledWith("/bff/configurations");
    const first = wrapper.find('a[href="/configurations/3"]');
    expect(first.find('[data-test="title"]').text()).toBe("Sitzungen");
    expect(first.text()).toContain("Goslar");
    // without a title the id is the link text
    expect(wrapper.find('a[href="/configurations/4"] [data-test="title"]').text()).toBe("4");
    expect(wrapper.find('[data-test="organizations"]').text()).toContain("Goslar");
  });

  it("creates a configuration and opens its form", async () => {
    GET.mockResolvedValue(list);
    POST.mockResolvedValue({ data: { id: 12 } });
    const { wrapper, router } = await mountPage(ConfigurationsPage);

    await wrapper.find('[data-test="organizations"] button').trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/configurations", {
      body: { app_installation_id: 9 },
    });
    expect(router.currentRoute.value.fullPath).toBe("/configurations/12/update");
  });

  it("shows the server error when creating fails", async () => {
    GET.mockResolvedValue(list);
    POST.mockResolvedValue({ error: { name: "Not Found", message: "Nope" } });
    const { wrapper, router } = await mountPage(ConfigurationsPage);

    await wrapper.find('[data-test="organizations"] button').trigger("click");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Nope");
    expect(router.currentRoute.value.fullPath).toBe("/configurations");
  });

  it("shows the message a previous page left", async () => {
    GET.mockResolvedValue(list);
    setFlash("Configuration deleted");
    await mountPage(ConfigurationsPage);

    expect(success).toHaveBeenCalledWith("Configuration deleted");
  });

  it("explains an empty list", async () => {
    GET.mockResolvedValue({ data: { configurations: [], app_installations: [] } });
    const { wrapper } = await mountPage(ConfigurationsPage);

    expect(wrapper.find('[data-test="empty"]').text()).toContain("No configurations yet");
    expect(wrapper.find('[data-test="no-organizations"]').exists()).toBe(true);
  });

  it("shows an error when the list cannot be loaded", async () => {
    GET.mockResolvedValue({ error: undefined });
    const { wrapper } = await mountPage(ConfigurationsPage);

    expect(wrapper.find(".alert-danger").text()).toBe("Error");
    expect(wrapper.find("h1").exists()).toBe(false);
  });
});
