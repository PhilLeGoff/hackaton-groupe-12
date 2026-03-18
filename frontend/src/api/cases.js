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

export const createCase = async (data) => {
  const response = await api.post("/api/cases", data);
  return response.data;
};

export const getAutofill = async (id) => {
  const response = await api.get(`/api/cases/${id}/autofill`);
  return response.data;
};

export const getDocumentsByCase = async (caseId) => {
  const response = await api.get(`/api/documents?case_id=${caseId}&limit=100`);
  return response.data;
};
