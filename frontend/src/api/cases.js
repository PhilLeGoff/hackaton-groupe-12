import { api } from "./axios";

export const getCases = async () => {
  try {
    const response = await api.get("/api/cases");
    return response.data;
  } catch (error) {
    console.error("API getCases error:", error);
    throw error;
  }
};

export const getCaseById = async (id) => {
  try {
    const response = await api.get(`/api/cases/${id}`);
    return response.data;
  } catch (error) {
    console.error("API getCaseById error:", error);
    throw error;
  }
};

export const getAutofill = async (id) => {
  const response = await api.get(`/api/cases/${id}/autofill`);
  return response.data;
};
