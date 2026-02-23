import api from "./client";

export const dashboardApi = {
  getStats: () => api.get("/dashboard/dashboard-stats").then((r) => r.data),
  getAlerts: () => api.get("/dashboard/alerts").then((r) => r.data),
  getToday: () => api.get("/dashboard/today").then((r) => r.data),
};
