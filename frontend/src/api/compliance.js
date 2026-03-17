import { api } from "./axios";

export const getComplianceByCaseId = async (caseId) => {
  const response = await api.get(`/compliance/${caseId}`);
  return response.data;
};