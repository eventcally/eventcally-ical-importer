import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("@/shared/boot", () => ({
  boot: { base: "/", locale: "en", csrfToken: "x", loginUrl: "/login" },
}));

const GET = vi.fn();
vi.mock("@/shared/api", () => ({
  api: { GET: (...a: unknown[]) => GET(...a) },
}));

import { mountPage } from "../testing";
import RunPage from "./RunPage.vue";

beforeEach(() => {
  GET.mockReset();
  document.body.innerHTML = "";
});

const mountIt = () => mountPage(RunPage, { id: 3, runId: 8 }, "/configurations/3/runs/8");

describe("RunPage", () => {
  it("shows the settings, the counts and the log", async () => {
    GET.mockResolvedValue({
      data: {
        id: 8,
        configuration_id: 3,
        configuration_title: "Sitzungen",
        created_at: "2026-01-17T16:00:00Z",
        configuration_settings: { url: "https://example.com/feed.ics" },
        status: "success",
        failure_event_count: 0,
        skipped_event_count: 4,
        new_event_count: 2,
        updated_event_count: 1,
        unchanged_event_count: 4,
        deleted_event_count: 0,
        log_entries: [
          {
            id: 1,
            created_at: "2026-01-17T16:00:01Z",
            message: "Event importiert",
            type: "vevent",
            context: { event: { name: "Sitzung" } },
          },
        ],
      },
    });
    const { wrapper } = await mountIt();

    expect(GET).toHaveBeenCalledWith("/bff/configurations/{id}/runs/{run_id}", {
      params: { path: { id: 3, run_id: 8 } },
    });
    expect(wrapper.find("h1").text()).toBe("Run 8");
    expect(wrapper.find('a[href="/configurations/3"]').text()).toBe("Configuration Sitzungen");
    expect(wrapper.find('[data-test="status"]').text()).toBe("success");
    // Europe/Berlin, whatever the machine's time zone is
    expect(wrapper.find('[data-test="created-at"]').text()).toContain("5:00:00");
    expect(wrapper.find('[data-test="settings"] pre').text()).toContain(
      '"url": "https://example.com/feed.ics"',
    );
    expect(wrapper.find('[data-test="skipped_event_count"]').text()).toBe("Skipped4");
    expect(wrapper.find('[data-test="new_event_count"] .stat-value').classes()).toContain(
      "text-success",
    );
    // a zero is shown muted, also for failures
    expect(wrapper.find('[data-test="failure_event_count"] .stat-value').classes()).toContain(
      "text-secondary",
    );
    const entry = wrapper.find('[data-test="log-entries"] li');
    expect(entry.text()).toContain("Event importiert");
    expect(entry.text()).toContain("vevent");
    expect(entry.find("pre").text()).toContain('"name": "Sitzung"');
  });

  it("shows the error of a missing run", async () => {
    GET.mockResolvedValue({ error: { name: "Not Found", message: "Gone" } });
    const { wrapper } = await mountIt();

    expect(wrapper.find(".alert-danger").text()).toBe("Gone");
    expect(wrapper.find("h1").exists()).toBe(false);
  });
});
