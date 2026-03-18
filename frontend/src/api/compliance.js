import { api } from "./axios";

export const getCompliances = async () => {
  try {
    const response = await api.get("/api/compliances");
    return response.data;
  } catch (error) {
    console.error("API getCompliances error:", error);
    throw error;
  }
};

export const getComplianceById = async (id) => {
  try {
    const response = await api.get(`/api/compliances/${id}`);
    return response.data;
  } catch (error) {
    console.error("API getComplianceById error:", error);
    throw error;
  }
};

export const getComplianceByCaseId = async (caseId) => {
  const response = await api.get(`/api/compliances/case/${caseId}`);
  return response.data;
};

export const updateCompliance = async (id, decision) => {
  const response = await api.put(`/api/compliances/${id}`, { decision });
  return response.data;
};
