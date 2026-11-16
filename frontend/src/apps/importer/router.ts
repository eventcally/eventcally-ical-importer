import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { boot } from "@/shared/boot";
import NotFoundPage from "@/shared/NotFoundPage.vue";
import ConfigurationEditPage from "./pages/ConfigurationEditPage.vue";
import ConfigurationPage from "./pages/ConfigurationPage.vue";
import ConfigurationsPage from "./pages/ConfigurationsPage.vue";
import RunPage from "./pages/RunPage.vue";

// Every URL here has a Flask shell with the same path (project/views/configuration.py).
export const routes: RouteRecordRaw[] = [
  { path: "/configurations", name: "configurations", component: ConfigurationsPage },
  {
    path: "/configurations/:id(\\d+)",
    name: "configuration",
    component: ConfigurationPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  {
    path: "/configurations/:id(\\d+)/update",
    name: "configuration-update",
    component: ConfigurationEditPage,
    props: (route) => ({ id: Number(route.params.id) }),
  },
  {
    path: "/configurations/:id(\\d+)/runs/:runId(\\d+)",
    name: "run",
    component: RunPage,
    props: (route) => ({ id: Number(route.params.id), runId: Number(route.params.runId) }),
  },
  { path: "/:pathMatch(.*)*", name: "not-found", component: NotFoundPage },
];

export const router = createRouter({
  history: createWebHistory(boot.base),
  routes,
});
