import { api } from "./axios";

export const getDocumentById = async (id) => {
  const response = await api.get(`/documents/${id}`);
  return response.data;
};

export const getDocumentExtraction = async (id) => {
  const response = await api.get(`/documents/${id}/extraction`);
  return response.data;
};