import api from "./client";

export interface Appointment {
  id: number;
  client_id: number;
  client_name?: string;
  service_type: string;
  duration_minutes: number;
  price?: number;
  status: "scheduled" | "completed" | "cancelled" | "no_show" | "needs_review";
  start_datetime: string;
  end_datetime: string;
  notes?: string;
  deposit_paid: boolean;
  google_event_id?: string;
}

export interface AppointmentCreate {
  client_id: number;
  service_type: string;
  duration_minutes: number;
  price?: number;
  start_datetime: string;
  notes?: string;
  deposit_paid?: boolean;
}

export const appointmentsApi = {
  list: (params?: {
    start?: string;
    end?: string;
    status?: string;
    client_id?: number;
  }) => api.get<Appointment[]>("/appointments", { params }).then((r) => r.data),

  get: (id: number) =>
    api.get<Appointment>(`/appointments/${id}`).then((r) => r.data),

  create: (data: AppointmentCreate) =>
    api.post<Appointment>("/appointments", data).then((r) => r.data),

  update: (id: number, data: Partial<AppointmentCreate>) =>
    api.put<Appointment>(`/appointments/${id}`, data).then((r) => r.data),

  cancel: (id: number, reason?: string) =>
    api
      .delete(`/appointments/${id}`, { data: { reason } })
      .then((r) => r.data),

  getUpcoming: () =>
    api.get<Appointment[]>("/appointments/upcoming").then((r) => r.data),

  getToday: () =>
    api.get<Appointment[]>("/appointments/today").then((r) => r.data),

  complete: (id: number) =>
    api.post(`/appointments/${id}/complete`).then((r) => r.data),

  noShow: (id: number) =>
    api.post(`/appointments/${id}/no-show`).then((r) => r.data),
};
