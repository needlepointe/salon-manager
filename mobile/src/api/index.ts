import api from "./client";

export const dashboardApi = {
  getStats: () => api.get("/dashboard/dashboard-stats").then((r) => r.data),
  getAlerts: () => api.get("/dashboard/alerts").then((r) => r.data),
  getToday: () => api.get("/dashboard/today").then((r) => r.data),
};

export const clientsApi = {
  list: (search?: string) =>
    api.get("/clients", { params: { search } }).then((r) => r.data),
  getLapsed: () => api.get("/clients/lapsed").then((r) => r.data),
  sendOutreach: (id: number) =>
    api.post(`/clients/${id}/sms-outreach`).then((r) => r.data),
};

export const appointmentsApi = {
  getToday: () => api.get("/dashboard/today").then((r) => r.data),
  getUpcoming: () => api.get("/appointments/upcoming").then((r) => r.data),
  complete: (id: number) =>
    api.post(`/appointments/${id}/complete`).then((r) => r.data),
  noShow: (id: number) =>
    api.post(`/appointments/${id}/no-show`).then((r) => r.data),
};

export const aftercareApi = {
  getPending: () => api.get("/aftercare/pending").then((r) => r.data),
  sendD3: (id: number) => api.post(`/aftercare/${id}/send-d3`).then((r) => r.data),
  sendW2: (id: number) => api.post(`/aftercare/${id}/send-w2`).then((r) => r.data),
};

export const leadsApi = {
  list: () => api.get("/leads").then((r) => r.data),
  getPipelineSummary: () => api.get("/leads/pipeline-summary").then((r) => r.data),
  qualify: (id: number) => api.post(`/leads/${id}/qualify`).then((r) => r.data),
};

export const inventoryApi = {
  getAlerts: () => api.get("/inventory/alerts").then((r) => r.data),
  listProducts: () => api.get("/inventory/products").then((r) => r.data),
};
