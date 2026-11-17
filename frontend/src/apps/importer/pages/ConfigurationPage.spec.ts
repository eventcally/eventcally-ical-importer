import { flushPromises } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login", eventcallySiteName: "Goslar Events" },
}));

const GET = vi.fn();
const POST = vi.fn();
vi.mock("@/shared/api", () => ({
  api: {
    GET: (...a: unknown[]) => GET(...a),
    POST: (...a: unknown[]) => POST(...a),
  },
}));

import { mountPage } from "../testing";
import ConfigurationPage from "./ConfigurationPage.vue";

const detail = (runs: object[] = []) => ({
  data: {
    id: 3,
    title: "Sitzungen",
    url: "https://example.com/feed.ics",
    organization_name: "Goslar",
    runs,
    imported_events: [
      {
        id: 1,
        vevent_uid: "uid-1",
        eventcally_event_id: "12",
        eventcally_url: "http://eventcally.test/event/12",
        event: { name: "Sitzung" },
      },
    ],
  },
});

const run = {
  id: 8,
  created_at: "2026-01-17T16:00:00Z",
  status: "success",
  new_event_count: 2,
  updated_event_count: 1,
  deleted_event_count: 0,
  failure_event_count: 0,
};

beforeEach(() => {
  [GET, POST].forEach((f) => f.mockReset());
  document.body.innerHTML = "";
  vi.useFakeTimers();
});
afterEach(() => vi.useRealTimers());

const mountIt = () => mountPage(ConfigurationPage, { id: 3 }, "/configurations/3");

describe("ConfigurationPage", () => {
  it("shows the configuration, its runs and imported events", async () => {
    GET.mockResolvedValue(detail([run]));
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith("/bff/configurations/{id}", {
      params: { path: { id: 3 } },
    });
    expect(wrapper.find("h1").text()).toBe("Configuration Sitzungen");
    expect(wrapper.find('[data-test="url"]').attributes("href")).toBe(
      "https://example.com/feed.ics",
    );
    expect(wrapper.find('[data-test="runs"] [data-test="status"]').classes()).toContain(
      "text-bg-success",
    );
    expect(wrapper.find('a[href="/configurations/3/update"]').text()).toBe("Edit configuration");
    const link = wrapper.find('a[href="/configurations/3/runs/8"]');
    // Europe/Berlin, whatever the machine's time zone is
    expect(link.text()).toContain("5:00:00");
    expect(link.text()).toContain("Run 8");
    const imported = wrapper.find('[data-test="imported-events"]');
    expect(imported.findAll("th")[1].text()).toBe("Goslar Events link");
    expect(imported.find("a").attributes("href")).toBe("http://eventcally.test/event/12");
    expect(imported.find("td.json pre").text()).toContain('"name": "Sitzung"');
  });

  it("explains the empty sections", async () => {
    const empty = detail();
    GET.mockResolvedValue({
      data: { ...empty.data, url: null, imported_events: [] },
    });
    const { wrapper } = await mountIt();

    expect(wrapper.find('[data-test="no-url"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="no-runs"]').text()).toBe("No runs yet");
    expect(wrapper.find('[data-test="no-imported-events"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="runs"]').exists()).toBe(false);
  });

  it("starts a run, polls until it is ready and reloads", async () => {
    GET.mockResolvedValueOnce(detail());
    const { wrapper } = await mountIt();

    POST.mockResolvedValue({ data: { id: "run-3-abc" } });
    GET.mockResolvedValueOnce({ data: { ready: false, successful: null } })
      .mockResolvedValueOnce({ data: { ready: true, successful: true } })
      .mockResolvedValueOnce(detail([run]));

    const button = wrapper.find('[data-test="start-run"]');
    await button.trigger("click");
    await flushPromises();

    expect(POST).toHaveBeenCalledWith("/bff/configurations/{id}/run-jobs", {
      params: { path: { id: 3 } },
    });
    expect(button.attributes("disabled")).toBeDefined();
    expect(wrapper.find('a[href="/configurations/3/runs/8"]').exists()).toBe(false);

    await vi.advanceTimersByTimeAsync(500);
    await flushPromises();

    expect(GET).toHaveBeenCalledWith("/bff/configurations/{id}/run-jobs/{job_id}", {
      params: { path: { id: 3, job_id: "run-3-abc" } },
    });
    expect(wrapper.find('a[href="/configurations/3/runs/8"]').exists()).toBe(true);
    expect(button.attributes("disabled")).toBeUndefined();
  });

  it("shows an error when the run cannot be started", async () => {
    GET.mockResolvedValueOnce(detail());
    const { wrapper } = await mountIt();
    POST.mockResolvedValue({ error: { name: "Bad Request", message: "Nope" } });

    await wrapper.find('[data-test="start-run"]').trigger("click");
    await flushPromises();

    expect(wrapper.find(".alert-danger").text()).toBe("Nope");
    expect(wrapper.find('[data-test="start-run"]').attributes("disabled")).toBeUndefined();
  });
});
