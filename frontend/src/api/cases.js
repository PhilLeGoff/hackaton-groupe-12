import { api } from "./axios";

export const getCases = async () => {
  const response = await api.get("/cases");
  return response.data;
};

export const getCaseById = async (id) => {
  const response = await api.get(`/cases/${id}`);
  return response.data;
};