import axios from "axios";

// Change this to your Railway URL after deployment
// e.g. "https://salon-api.up.railway.app"
export const API_BASE_URL =
  process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: { "Content-Type": "application/json" },
  timeout: 15000,
});

export default api;
