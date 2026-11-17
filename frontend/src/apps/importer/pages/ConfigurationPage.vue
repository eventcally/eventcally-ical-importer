<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { boot } from "@/shared/boot";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import JsonDetails from "@/shared/JsonDetails.vue";
import StatusBadge from "@/shared/StatusBadge.vue";
import { errorMessage } from "@/shared/apiError";
import { formatDateTime } from "@/shared/format";

type ConfigurationDetail = components["schemas"]["ConfigurationDetail"];

const POLL_MS = 500;

const props = defineProps<{ id: number }>();

const { t, locale } = useI18n();

const configuration = ref<ConfigurationDetail | null>(null);
const error = ref<string | null>(null);
const running = ref(false);
let timer: ReturnType<typeof setTimeout> | undefined;

async function load() {
  const { data, error: err } = await api.GET("/bff/configurations/{id}", {
    params: { path: { id: props.id } },
  });
  if (data) configuration.value = data;
  else error.value = errorMessage(err, t("Error"));
}

onMounted(load);
onBeforeUnmount(() => clearTimeout(timer));

async function startRun() {
  if (running.value) return;
  running.value = true;
  error.value = null;

  const { data, error: err } = await api.POST("/bff/configurations/{id}/run-jobs", {
    params: { path: { id: props.id } },
  });
  if (!data) {
    running.value = false;
    error.value = errorMessage(err, t("Error"));
    return;
  }
  poll(data.id);
}

async function poll(jobId: string) {
  const { data, error: err } = await api.GET("/bff/configurations/{id}/run-jobs/{job_id}", {
    params: { path: { id: props.id, job_id: jobId } },
  });
  if (!data) {
    running.value = false;
    error.value = errorMessage(err, t("Error"));
    return;
  }
  if (!data.ready) {
    timer = setTimeout(() => poll(jobId), POLL_MS);
    return;
  }
  // The run itself reports its failures; show whatever it stored.
  await load();
  running.value = false;
}
</script>

<template>
  <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

  <template v-if="configuration">
    <AppBreadcrumb
      :items="[
        { label: t('Configurations'), to: { name: 'configurations' } },
        { label: String(configuration.title || configuration.id) },
      ]"
    />
    <div class="d-flex flex-wrap align-items-start gap-2 mb-4">
      <div class="me-auto">
        <h1>{{ t("Configuration") }} {{ configuration.title || configuration.id }}</h1>
        <div class="text-secondary mt-1">
          <i class="fas fa-building me-1" aria-hidden="true"></i>{{ configuration.organization_name }}
        </div>
      </div>
      <router-link
        :to="{ name: 'configuration-update', params: { id: configuration.id } }"
        class="btn btn-outline-secondary"
        ><i class="fas fa-pen me-1" aria-hidden="true"></i>{{ t("Edit configuration") }}</router-link
      >
      <button type="button" class="btn btn-primary" :disabled="running" data-test="start-run" @click="startRun">
        <template v-if="running">
          <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
          {{ t("Loading...") }}
        </template>
        <template v-else><i class="fas fa-play me-1" aria-hidden="true"></i>{{ t("Start run") }}</template>
      </button>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body d-flex align-items-center">
        <i class="fas fa-link fa-fw text-secondary me-3" aria-hidden="true"></i>
        <div class="text-truncate">
          <div class="small text-secondary">{{ t("Feed URL") }}</div>
          <a
            v-if="configuration.url"
            :href="configuration.url"
            target="_blank"
            rel="noopener noreferrer"
            class="font-monospace small"
            data-test="url"
            >{{ configuration.url }}</a
          >
          <span v-else class="text-secondary" data-test="no-url">{{ t("No feed URL yet") }}</span>
        </div>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-header bg-transparent d-flex align-items-center py-3">
        <h2>{{ t("Runs") }}</h2>
        <span class="badge rounded-pill text-bg-secondary ms-2">{{ configuration.runs.length }}</span>
      </div>
      <div v-if="configuration.runs.length" class="table-responsive">
        <table class="table table-hover align-middle" data-test="runs">
          <thead>
            <tr>
              <th>{{ t("Run") }}</th>
              <th>{{ t("Status") }}</th>
              <th class="num">{{ t("New") }}</th>
              <th class="num">{{ t("Updated") }}</th>
              <th class="num">{{ t("Deleted") }}</th>
              <th class="num">{{ t("Failures") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in configuration.runs" :key="run.id">
              <td>
                <router-link
                  :to="{ name: 'run', params: { id: configuration.id, runId: run.id } }"
                  class="text-decoration-none"
                  >{{ formatDateTime(run.created_at, locale) }}
                  <span class="text-secondary">· {{ t("Run") }} {{ run.id }}</span></router-link
                >
              </td>
              <td><StatusBadge :status="run.status" /></td>
              <td class="num">{{ run.new_event_count }}</td>
              <td class="num">{{ run.updated_event_count }}</td>
              <td class="num">{{ run.deleted_event_count }}</td>
              <td class="num" :class="{ 'text-danger fw-semibold': run.failure_event_count }">
                {{ run.failure_event_count }}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="card-body text-secondary" data-test="no-runs">{{ t("No runs yet") }}</div>
    </div>

    <div class="card shadow-sm">
      <div class="card-header bg-transparent d-flex align-items-center py-3">
        <h2>{{ t("Imported events") }}</h2>
        <span class="badge rounded-pill text-bg-secondary ms-2">{{
          configuration.imported_events.length
        }}</span>
      </div>
      <div v-if="configuration.imported_events.length" class="table-responsive">
        <table class="table align-middle" data-test="imported-events">
          <thead>
            <tr>
              <th>{{ t("Vevent UID") }}</th>
              <th>{{ t("%(eventcally_site_name)s link", { eventcally_site_name: boot.eventcallySiteName }) }}</th>
              <th>{{ t("Data") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="importedEvent in configuration.imported_events" :key="importedEvent.id">
              <td class="font-monospace small text-break">{{ importedEvent.vevent_uid }}</td>
              <td class="fit">
                <a :href="importedEvent.eventcally_url" target="_blank" rel="noopener noreferrer"
                  >{{ importedEvent.eventcally_event_id
                  }}<i class="fas fa-external-link-alt fa-xs ms-1" aria-hidden="true"></i
                ></a>
              </td>
              <td class="json"><JsonDetails :value="importedEvent.event" :label="t('Show data')" /></td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="card-body text-secondary" data-test="no-imported-events">
        {{ t("No imported events yet") }}
      </div>
    </div>
  </template>
</template>
