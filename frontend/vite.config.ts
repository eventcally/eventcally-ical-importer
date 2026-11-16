import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

const src = fileURLToPath(new URL("./src", import.meta.url));

export default defineConfig({
  plugins: [vue()],
  base: "/static/dist/",
  resolve: { alias: { "@": src } },
  build: {
    outDir: "../project/static/dist",
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        importer: "src/apps/importer/main.ts",
      },
    },
  },
  // 5175, not Vite's 5173: the eventcally dev stack runs next to this one.
  server: { port: 5175, strictPort: true, origin: "http://localhost:5175" },
  test: { environment: "jsdom", include: ["src/**/*.spec.ts", "scripts/**/*.spec.ts"] },
});
