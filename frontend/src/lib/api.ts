import axios, { AxiosError } from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10_000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ─── Request Interceptor ────────────────────────────────────────────────────
api.interceptors.request.use(
  (config) => {
    // Attach auth token here once auth is implemented:
    // const token = localStorage.getItem('asterion-token')
    // if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  },
  (error) => Promise.reject(error),
)

// ─── Response Interceptor ───────────────────────────────────────────────────
api.interceptors.response.use(
  (response) => {
    // If the response is wrapped in our APIResponse format, unwrap it
    if (response.data && typeof response.data === 'object' && response.data.success === true && 'data' in response.data) {
      response.data = response.data.data;
    }
    return response;
  },
  (error: AxiosError<{ detail?: string | { msg: string }[]; error?: { message: string } }>) => {
    // Normalize FastAPI validation errors and plain detail strings into a
    // human-readable message that can be shown directly in ErrorCard.
    if (error.response?.data?.error?.message) {
      error.message = error.response.data.error.message;
    } else if (error.response?.data?.detail) {
      const detail = error.response.data.detail;
      if (typeof detail === 'string') {
        error.message = detail;
      } else if (Array.isArray(detail)) {
        // FastAPI 422 Unprocessable Entity returns an array of validation errors
        error.message = detail.map((d) => d.msg).join('; ');
      }
    } else if (!error.response) {
      // Network error — no response received at all
      error.message = 'Unable to reach the backend. Is the server running?';
    }
    return Promise.reject(error);
  },
)
