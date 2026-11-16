<script setup lang="ts">
import { computed } from "vue";
import { formatJson } from "./format";

// Read-only data (JSON, or a string as is) folded behind a summary line.
const props = defineProps<{ value: unknown; label: string; open?: boolean }>();

const text = computed(() =>
  typeof props.value === "string" ? props.value : formatJson(props.value),
);
</script>

<template>
  <details v-if="text" :open="open">
    <summary class="small text-secondary">{{ label }}</summary>
    <pre class="code-box mt-1">{{ text }}</pre>
  </details>
</template>
