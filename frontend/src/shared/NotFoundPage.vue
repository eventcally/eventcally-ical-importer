<script setup lang="ts">
import { useI18n } from "vue-i18n";

const { t } = useI18n();
</script>

<template>
  <div class="alert alert-warning" role="alert">
    <i class="fas fa-exclamation-triangle me-2" aria-hidden="true"></i
    >{{ t("The requested resource was not found") }}
  </div>
</template>
