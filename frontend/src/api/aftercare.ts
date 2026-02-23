import api from "./client";

export const aftercareApi = {
  list: () => api.get("/aftercare").then((r) => r.data),
  getPending: () => api.get("/aftercare/pending").then((r) => r.data),
  sendD3: (id: number) =>
    api.post(`/aftercare/${id}/send-d3`).then((r) => r.data),
  sendW2: (id: number) =>
    api.post(`/aftercare/${id}/send-w2`).then((r) => r.data),
  recordResponse: (
    id: number,
    data: { response_type: "d3" | "w2"; response_text: string }
  ) =>
    api
      .put(`/aftercare/${id}/response`, null, { params: data })
      .then((r) => r.data),
};
