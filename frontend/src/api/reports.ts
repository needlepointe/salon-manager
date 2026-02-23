import api from "./client";

export const reportsApi = {
  list: () => api.get("/reports").then((r) => r.data),
  get: (month: string) => api.get(`/reports/${month}`).then((r) => r.data),
  generate: (month: string) =>
    api.post(`/reports/${month}/generate`).then((r) => r.data),
};
