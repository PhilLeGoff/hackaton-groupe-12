import { api } from "./axios";

export const getComplianceByCaseId = async (caseId) => {
  const response = await api.get(`/api/compliances/${caseId}`);
  return response.data;
};