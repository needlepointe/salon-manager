import api from "./client";

export interface Lead {
  id: number;
  name: string;
  phone?: string;
  email?: string;
  source?: string;
  hair_length?: string;
  hair_texture?: string;
  desired_length?: string;
  desired_color?: string;
  extension_type?: string;
  budget_range?: string;
  timeline?: string;
  ai_qualification_score?: number;
  ai_qualification_tier?: string;
  pipeline_stage:
    | "new"
    | "contacted"
    | "qualified"
    | "quoted"
    | "follow_up"
    | "booked"
    | "lost";
  quote_amount?: number;
  quote_text?: string;
  follow_up_count: number;
  next_follow_up_at?: string;
  notes?: string;
  created_at: string;
}

export interface LeadCreate {
  name: string;
  phone?: string;
  email?: string;
  source?: string;
  hair_length?: string;
  hair_texture?: string;
  desired_length?: string;
  desired_color?: string;
  extension_type?: string;
  budget_range?: string;
  timeline?: string;
  notes?: string;
}

export const leadsApi = {
  list: (params?: { stage?: string }) =>
    api.get<Lead[]>("/leads", { params }).then((r) => r.data),

  get: (id: number) => api.get<Lead>(`/leads/${id}`).then((r) => r.data),

  create: (data: LeadCreate) =>
    api.post<Lead>("/leads", data).then((r) => r.data),

  update: (id: number, data: Partial<Lead>) =>
    api.put<Lead>(`/leads/${id}`, data).then((r) => r.data),

  delete: (id: number) => api.delete(`/leads/${id}`).then((r) => r.data),

  getPipelineSummary: () =>
    api.get("/leads/pipeline-summary").then((r) => r.data),

  qualify: (id: number) =>
    api.post(`/leads/${id}/qualify`).then((r) => r.data),

  sendQuote: (id: number) =>
    api.post(`/leads/${id}/send-quote`).then((r) => r.data),

  sendFollowUp: (id: number) =>
    api.post(`/leads/${id}/follow-up`).then((r) => r.data),
};
