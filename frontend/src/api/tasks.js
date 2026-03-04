import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "";

const api = axios.create({
  baseURL: `${BASE_URL}/api`,
  headers: { "Content-Type": "application/json" },
});

export const taskApi = {
  list: () => api.get("/tasks/"),
  get: (id) => api.get(`/tasks/${id}/`),
  create: (data) => api.post("/tasks/", data),
  update: (id, data) => api.put(`/tasks/${id}/`, data),
  patch: (id, data) => api.patch(`/tasks/${id}/`, data),
  delete: (id) => api.delete(`/tasks/${id}/`),
  upload: (id, file) => {
    const form = new FormData();
    form.append("attachment", file);
    return api.post(`/tasks/${id}/upload/`, form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  health: () => api.get("/health/"),
};
