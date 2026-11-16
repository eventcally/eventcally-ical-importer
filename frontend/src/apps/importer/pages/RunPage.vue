<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import JsonDetails from "@/shared/JsonDetails.vue";
import StatusBadge from "@/shared/StatusBadge.vue";
import { errorMessage } from "@/shared/apiError";
import { formatDateTime } from "@/shared/format";

type RunDetail = components["schemas"]["RunDetail"];

const props = defineProps<{ id: number; runId: number }>();

const { t, locale } = useI18n();

const run = ref<RunDetail | null>(null);
const error = ref<string | null>(null);

// Literal t() calls so the extractor finds the labels.
const counts = computed(() => [
  { name: "new_event_count", label: t("New"), tone: "text-success" },
  { name: "updated_event_count", label: t("Updated"), tone: "text-primary" },
  { name: "deleted_event_count", label: t("Deleted"), tone: "text-body" },
  { name: "unchanged_event_count", label: t("Unchanged"), tone: "text-secondary" },
  { name: "skipped_event_count", label: t("Skipped"), tone: "text-secondary" },
  { name: "failure_event_count", label: t("Failures"), tone: "text-danger" },
] as const);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/configurations/{id}/runs/{run_id}", {
    params: { path: { id: props.id, run_id: props.runId } },
  });
  if (data) run.value = data;
  else error.value = errorMessage(err, t("Error"));
});
</script>

<template>
  <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

  <template v-if="run">
    <AppBreadcrumb
      :items="[
        { label: t('Configurations'), to: { name: 'configurations' } },
        {
          label: `${t('Configuration')} ${run.configuration_title || run.configuration_id}`,
          to: { name: 'configuration', params: { id: run.configuration_id } },
        },
        { label: `${t('Run')} ${run.id}` },
      ]"
    />
    <div class="d-flex flex-wrap align-items-center gap-2 mb-4">
      <h1>{{ t("Run") }} {{ run.id }}</h1>
      <StatusBadge :status="run.status" />
      <span class="text-secondary ms-auto" data-test="created-at">
        <i class="far fa-clock me-1" aria-hidden="true"></i>{{ formatDateTime(run.created_at, locale) }}
      </span>
    </div>

    <div class="row row-cols-2 row-cols-md-3 row-cols-xl-6 g-3 mb-4" data-test="counts">
      <div v-for="count in counts" :key="count.name" class="col">
        <div class="card shadow-sm stat-tile h-100" :data-test="count.name">
          <div class="card-body py-3">
            <div class="small text-secondary">{{ count.label }}</div>
            <div class="stat-value" :class="run[count.name] ? count.tone : 'text-secondary'">
              {{ run[count.name] ?? 0 }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="card shadow-sm mb-4">
      <div class="card-body" data-test="settings">
        <JsonDetails :value="run.configuration_settings" :label="t('Configuration settings of this run')" />
      </div>
    </div>

    <div class="card shadow-sm">
      <div class="card-header bg-transparent d-flex align-items-center py-3">
        <h2>{{ t("Log entries") }}</h2>
        <span class="badge rounded-pill text-bg-secondary ms-2">{{ run.log_entries.length }}</span>
      </div>
      <ul v-if="run.log_entries.length" class="list-group list-group-flush" data-test="log-entries">
        <li v-for="entry in run.log_entries" :key="entry.id ?? undefined" class="list-group-item py-3">
          <div class="d-flex flex-wrap align-items-baseline gap-2">
            <span class="text-break me-auto">{{ entry.message }}</span>
            <span v-if="entry.type" class="badge text-bg-light border">{{ entry.type }}</span>
            <span class="small text-secondary text-nowrap">{{ formatDateTime(entry.created_at, locale) }}</span>
          </div>
          <JsonDetails class="mt-1" :value="entry.context" :label="t('Show data')" />
        </li>
      </ul>
      <div v-else class="card-body text-secondary" data-test="no-log-entries">
        {{ t("No log entries") }}
      </div>
    </div>
  </template>
</template>
