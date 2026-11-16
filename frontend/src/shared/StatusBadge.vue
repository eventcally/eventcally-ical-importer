<script setup lang="ts">
import { computed } from "vue";

// The status of a run as the importer stores it: "success" or "failure".
const props = defineProps<{ status: string | null | undefined }>();

const look = computed(() => {
  if (props.status === "success") return { variant: "text-bg-success", icon: "fa-check" };
  if (props.status === "failure") return { variant: "text-bg-danger", icon: "fa-times" };
  return { variant: "text-bg-secondary", icon: "fa-question" };
});
</script>

<template>
  <span v-if="status" class="badge rounded-pill" :class="look.variant" data-test="status">
    <i class="fas" :class="look.icon" aria-hidden="true"></i> {{ status }}
  </span>
</template>
