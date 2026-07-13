import axios from "axios";

// Relative path in dev (proxied to the backend by vite.config.ts's server.proxy,
// avoiding CORS entirely). In production there's no dev-server proxy, so
// VITE_API_BASE_URL should be set (e.g. on Vercel) to the deployed backend's
// full URL — the backend's CORS_ORIGINS must then include this frontend's
// origin.
const baseURL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
