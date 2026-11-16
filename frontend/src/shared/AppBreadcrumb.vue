<script setup lang="ts">
import type { RouteLocationRaw } from "vue-router";

defineProps<{ items: { label: string; to?: RouteLocationRaw }[] }>();
</script>

<template>
  <nav aria-label="breadcrumb">
    <ol class="breadcrumb small mb-2">
      <li
        v-for="(item, index) in items"
        :key="index"
        class="breadcrumb-item"
        :class="{ active: !item.to }"
        :aria-current="item.to ? undefined : 'page'"
      >
        <router-link v-if="item.to" :to="item.to" class="text-decoration-none">{{
          item.label
        }}</router-link>
        <template v-else>{{ item.label }}</template>
      </li>
    </ol>
  </nav>
</template>
