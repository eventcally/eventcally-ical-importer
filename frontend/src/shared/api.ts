import createClient, { type Middleware } from "openapi-fetch";
import type { paths } from "@/api/schema";
import { boot } from "./boot";

const UNSAFE = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export const authMiddleware: Middleware = {
  onRequest({ request }) {
    request.headers.set("Accept", "application/json");
    if (UNSAFE.has(request.method)) {
      request.headers.set("X-CSRFToken", boot.csrfToken);
    }
    return request;
  },
  onResponse({ response }) {
    // The session ended (or EventCally rejected the token): log in again.
    if (response.status === 401) {
      location.assign(boot.loginUrl);
    }
    return response;
  },
};

export const api = createClient<paths>({ baseUrl: "" });
api.use(authMiddleware);
