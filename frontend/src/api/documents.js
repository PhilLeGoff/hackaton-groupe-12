import { api } from "./axios";

export const getDocuments = async () => {
  const response = await api.get("/api/documents");
  return response.data;
};

export const getDocumentById = async (id) => {
  const response = await api.get(`/api/documents/${id}`);
  return response.data;
};