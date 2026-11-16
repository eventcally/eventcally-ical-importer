<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import type { components } from "@/api/schema";
import { api } from "@/shared/api";
import { errorMessage } from "@/shared/apiError";
import { useFlashNotice } from "@/shared/useFlashNotice";

type ConfigurationList = components["schemas"]["ConfigurationList"];

const { t } = useI18n();
const router = useRouter();
useFlashNotice();

const list = ref<ConfigurationList | null>(null);
const error = ref<string | null>(null);
const creatingFor = ref<number | null>(null);

onMounted(async () => {
  const { data, error: err } = await api.GET("/bff/configurations");
  if (data) list.value = data;
  else error.value = errorMessage(err, t("Error"));
});

async function create(appInstallationId: number) {
  if (creatingFor.value !== null) return;
  creatingFor.value = appInstallationId;
  error.value = null;

  const { data, error: err } = await api.POST("/bff/configurations", {
    body: { app_installation_id: appInstallationId },
  });
  creatingFor.value = null;

  if (data) {
    await router.push({ name: "configuration-update", params: { id: data.id } });
  } else {
    error.value = errorMessage(err, t("Error"));
  }
}
</script>

<template>
  <div v-if="error" class="alert alert-danger" role="alert">{{ error }}</div>

  <template v-if="list">
    <div class="d-flex align-items-center mb-3">
      <h1>{{ t("Configurations") }}</h1>
      <span class="badge rounded-pill text-bg-secondary ms-2">{{ list.configurations.length }}</span>
    </div>

    <div class="card shadow-sm mb-4">
      <div v-if="list.configurations.length" class="list-group list-group-flush" data-test="configurations">
        <router-link
          v-for="configuration in list.configurations"
          :key="configuration.id"
          :to="{ name: 'configuration', params: { id: configuration.id } }"
          class="list-group-item list-group-item-action d-flex align-items-center py-3"
        >
          <i class="fas fa-rss fa-fw text-primary me-3" aria-hidden="true"></i>
          <span class="me-auto">
            <span class="fw-semibold d-block" data-test="title">{{ configuration.title || configuration.id }}</span>
            <span class="small text-secondary">{{ configuration.organization_name }}</span>
          </span>
          <i class="fas fa-chevron-right text-secondary" aria-hidden="true"></i>
        </router-link>
      </div>
      <div v-else class="card-body text-center text-secondary py-5" data-test="empty">
        <i class="fas fa-rss fa-2x mb-3 d-block" aria-hidden="true"></i>
        {{ t("No configurations yet") }}
      </div>
    </div>

    <h2 class="mb-1">{{ t("Organizations") }}</h2>
    <p class="small text-secondary mb-3">
      {{ t("Create a configuration for one of your organizations.") }}
    </p>
    <div class="card shadow-sm">
      <ul v-if="list.app_installations.length" class="list-group list-group-flush" data-test="organizations">
        <li
          v-for="installation in list.app_installations"
          :key="installation.id"
          class="list-group-item d-flex align-items-center py-3"
        >
          <i class="fas fa-building fa-fw text-secondary me-3" aria-hidden="true"></i>
          <span class="me-auto">{{ installation.organization_name }}</span>
          <button
            type="button"
            class="btn btn-outline-primary btn-sm"
            :disabled="creatingFor !== null"
            @click="create(installation.id)"
          >
            <span
              v-if="creatingFor === installation.id"
              class="spinner-border spinner-border-sm"
              aria-hidden="true"
            ></span>
            <i v-else class="fas fa-plus" aria-hidden="true"></i>
            {{ t("Create configuration") }}
          </button>
        </li>
      </ul>
      <div v-else class="card-body text-secondary" data-test="no-organizations">
        {{ t("The app is not installed for any organization you administrate.") }}
      </div>
    </div>
  </template>
</template>
