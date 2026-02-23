import api from "./client";

export interface Client {
  id: number;
  full_name: string;
  phone: string;
  email?: string;
  notes?: string;
  last_visit_date?: string;
  total_visits: number;
  total_spent: number;
  is_lapsed: boolean;
  hair_profile?: Record<string, unknown>;
  created_at: string;
}

export interface ClientCreate {
  full_name: string;
  phone: string;
  email?: string;
  notes?: string;
  hair_profile?: Record<string, unknown>;
}

export const clientsApi = {
  list: (params?: { search?: string; page?: number; limit?: number }) =>
    api.get<Client[]>("/clients", { params }).then((r) => r.data),

  get: (id: number) => api.get<Client>(`/clients/${id}`).then((r) => r.data),

  create: (data: ClientCreate) =>
    api.post<Client>("/clients", data).then((r) => r.data),

  update: (id: number, data: Partial<ClientCreate>) =>
    api.put<Client>(`/clients/${id}`, data).then((r) => r.data),

  getLapsed: () => api.get<Client[]>("/clients/lapsed").then((r) => r.data),

  getTimeline: (id: number) =>
    api.get(`/clients/${id}/timeline`).then((r) => r.data),

  sendOutreach: (id: number) =>
    api.post(`/clients/${id}/sms-outreach`).then((r) => r.data),

  addToWaitlist: (data: {
    client_id: number;
    desired_service: string;
    desired_date_from?: string;
    desired_date_to?: string;
  }) => api.post("/clients/waitlist", data).then((r) => r.data),
};
