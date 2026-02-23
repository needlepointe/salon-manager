import axios from "axios";

// In production (Vercel), VITE_API_URL points to Railway backend.
// In development, requests proxy to localhost:8000 via vite.config.ts.
const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api/v1`
  : "/api/v1";

const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export default api;
