import axios from "axios";

const API_BASE = "http://localhost:8002/api";

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

export const getHealth = async () => {
  const response = await api.get("/health");
  return response.data;
};

export const getViolations = async (params) => {
  const response = await api.get("/violations", { params });
  return response.data;
};

export const getAnalytics = async () => {
  const response = await api.get("/analytics");
  return response.data;
};

export const detectImage = async (formData) => {
  const response = await api.post("/detect", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const exportReport = async (reportType) => {
  const response = await api.get(`/reports/${reportType}?format=csv`, {
    responseType: "blob",
  });
  return response.data;
};

export const getApiBase = () => API_BASE;

export default api;
