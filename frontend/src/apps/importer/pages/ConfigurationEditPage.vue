<script setup lang="ts">
import { BModal } from "bootstrap-vue-next";
import { computed, onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import AppBreadcrumb from "@/shared/AppBreadcrumb.vue";
import StatusBadge from "@/shared/StatusBadge.vue";
import { errorMessage, fieldErrors } from "@/shared/apiError";
import { setFlash } from "@/shared/flash";
import { formatJson } from "@/shared/format";
import { useNotify } from "@/shared/notify";

type ConfigurationForm = components["schemas"]["ConfigurationForm"];
type ConfigurationFormRead = components["schemas"]["ConfigurationFormRead"];
type RunPreview = components["schemas"]["RunPreview"];
type FieldName = keyof ConfigurationForm;

const props = defineProps<{ id: number }>();

const { t } = useI18n();
const router = useRouter();
const notify = useNotify();

const form = ref<ConfigurationFormRead | null>(null);
const values = ref<ConfigurationForm | null>(null);
const error = ref<string | null>(null);
const errors = ref<Record<string, string>>({});
const busy = ref<"save" | "preview" | "delete" | null>(null);
const preview = ref<RunPreview | null>(null);
const showDelete = ref(false);

// The labels are the field names, as the templates refer to them (`standard["name"]`).
const inputFields: { name: FieldName; type: string }[] = [
  { name: "title", type: "text" },
  { name: "identifier_tag", type: "text" },
  { name: "url", type: "url" },
];
const mapperFields = computed(() => (form.value?.mapper_fields ?? []) as FieldName[]);
const displayTitle = computed(() => form.value?.values.title || form.value?.id);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/configurations/{id}/form", {
    params: { path: { id: props.id } },
  });
  if (data) {
    form.value = data;
    values.value = { ...data.values };
  } else {
    error.value = errorMessage(err, t("Error"));
  }
});

function fail(err: unknown) {
  errors.value = fieldErrors(err) ?? {};
  error.value = errorMessage(err, t("Error"));
}

function begin(action: "save" | "preview" | "delete") {
  if (busy.value || !values.value) return false;
  busy.value = action;
  error.value = null;
  errors.value = {};
  return true;
}

async function save() {
  if (!begin("save")) return;
  const { error: err, response } = await api.PUT("/bff/configurations/{id}", {
    params: { path: { id: props.id } },
    body: values.value!,
  });
  busy.value = null;

  if (response.ok) {
    if (form.value) form.value.values = { ...values.value! };
    notify.success(t("Configuration saved"));
  } else {
    fail(err);
  }
}

async function runPreview() {
  if (!begin("preview")) return;
  preview.value = null;
  const { data, error: err } = await api.POST("/bff/configurations/{id}/preview", {
    params: { path: { id: props.id } },
    body: values.value!,
  });
  busy.value = null;

  if (data) preview.value = data;
  else fail(err);
}

async function remove() {
  if (!begin("delete")) return;
  const { error: err, response } = await api.POST("/bff/configurations/{id}/delete", {
    params: { path: { id: props.id } },
  });
  busy.value = null;

  if (response.ok) {
    showDelete.value = false;
    setFlash(t("Configuration deleted"));
    await router.replace({ name: "configurations" });
  } else {
    showDelete.value = false;
    fail(err);
  }
}

function close() {
  router.replace({ name: "configuration", params: { id: props.id } });
}

// The old page showed an empty cell for "no errors / hints".
function listJson(items: unknown): string {
  return Array.isArray(items) && items.length > 0 ? formatJson(items) : "";
}
</script>

<template>
  <div v-if="error" class="alert alert-danger" role="alert" data-test="error">{{ error }}</div>

  <template v-if="form && values">
    <AppBreadcrumb
      :items="[
        { label: t('Configurations'), to: { name: 'configurations' } },
        { label: String(displayTitle), to: { name: 'configuration', params: { id } } },
        { label: t('Update') },
      ]"
    />
    <div class="mb-4">
      <h1>{{ t("Update %(title)s", { title: displayTitle }) }}</h1>
      <div class="text-secondary mt-1">
        <i class="fas fa-building me-1" aria-hidden="true"></i>{{ form.organization_name }}
      </div>
    </div>

    <form id="form" novalidate @submit.prevent="save">
      <div class="card shadow-sm mb-4">
        <div class="card-header bg-transparent py-3">
          <h2>{{ t("Feed") }}</h2>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div
              v-for="field in inputFields"
              :key="field.name"
              :class="field.name === 'url' ? 'col-12' : 'col-md-6'"
            >
              <label class="form-label field-name mb-1" :for="field.name">{{ field.name }}</label>
              <input
                :id="field.name"
                v-model="values[field.name]"
                class="form-control"
                :class="{ 'is-invalid': errors[field.name] }"
                :name="field.name"
                :type="field.type"
              />
              <div v-if="errors[field.name]" class="invalid-feedback">{{ errors[field.name] }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="card shadow-sm mb-4">
        <div class="card-header bg-transparent py-3">
          <h2>{{ t("Field mapping") }}</h2>
          <div class="small text-secondary mt-1">
            {{ t("Jinja templates that build the event from the feed entry.") }}
          </div>
        </div>
        <div class="card-body">
          <div class="row g-3">
            <div v-for="name in mapperFields" :key="name" class="col-lg-6">
              <label class="form-label field-name mb-1" :for="name">{{ name }}</label>
              <textarea
                :id="name"
                v-model="values[name]"
                class="form-control template-field"
                :class="{ 'is-invalid': errors[name] }"
                :name="name"
                rows="1"
                spellcheck="false"
              ></textarea>
              <div v-if="errors[name]" class="invalid-feedback">{{ errors[name] }}</div>
            </div>
          </div>
        </div>
      </div>
    </form>

    <div class="action-bar shadow-sm d-flex flex-wrap gap-2 p-3 mb-4">
      <button type="submit" form="form" class="btn btn-primary" :disabled="busy !== null" data-test="save">
        <span v-if="busy === 'save'" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        <i v-else class="fas fa-save" aria-hidden="true"></i>
        {{ t("Save") }}
      </button>
      <button
        type="button"
        class="btn btn-outline-primary"
        :disabled="busy !== null"
        data-test="preview"
        @click="runPreview"
      >
        <span v-if="busy === 'preview'" class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        <i v-else class="fas fa-eye" aria-hidden="true"></i>
        {{ t("Preview") }}
      </button>
      <button type="button" class="btn btn-outline-secondary" data-test="close" @click="close">
        {{ t("Close") }}
      </button>
      <button
        type="button"
        class="btn btn-outline-danger ms-auto"
        :disabled="busy !== null"
        data-test="delete"
        @click="showDelete = true"
      >
        <i class="fas fa-trash-alt" aria-hidden="true"></i>
        {{ t("Delete configuration") }}
      </button>
    </div>

    <div v-if="preview" class="card shadow-sm" data-test="preview-table">
      <div class="card-header bg-transparent d-flex flex-wrap align-items-center gap-2 py-3">
        <h2 class="me-auto">{{ t("Preview") }}</h2>
        <span class="small text-secondary">{{ preview.log_entries.length }} {{ t("entries") }}</span>
        <StatusBadge :status="preview.status" />
      </div>
      <div class="table-responsive">
        <table class="table table-preview">
          <thead>
            <tr>
              <th>Vevent</th>
              <th>Standard</th>
              <th>Event</th>
              <th>Errors</th>
              <th>Hints</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(entry, index) in preview.log_entries" :key="index">
              <template v-if="entry.type === 'vevent' && entry.context">
                <td><pre class="code-box">{{ entry.context.vevent }}</pre></td>
                <td><pre class="code-box">{{ formatJson(entry.context.standard) }}</pre></td>
                <td><pre class="code-box">{{ formatJson(entry.context.event) }}</pre></td>
                <td>
                  <pre v-if="listJson(entry.context.errors)" class="code-box text-danger">{{
                    listJson(entry.context.errors)
                  }}</pre>
                </td>
                <td>
                  <pre v-if="listJson(entry.context.hints)" class="code-box">{{
                    listJson(entry.context.hints)
                  }}</pre>
                </td>
              </template>
              <td v-else colspan="5" class="text-danger">{{ entry.message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <BModal
      v-model="showDelete"
      :title="t('Delete configuration')"
      :ok-title="t('Delete configuration')"
      ok-variant="danger"
      :cancel-title="t('Cancel')"
      cancel-variant="outline-secondary"
      :ok-disabled="busy !== null"
      @ok.prevent="remove"
    >
      <p class="mb-0">{{ t("Delete configuration?") }}</p>
    </BModal>
  </template>
</template>
