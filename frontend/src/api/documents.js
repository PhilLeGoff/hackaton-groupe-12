import { api } from "./axios";

export const getDocuments = async () => {
  try {
    const response = await api.get("/api/documents");
    return response.data;
  } catch (error) {
    console.error("API getDocuments error:", error);
    throw error;
  }
};

export const getDocumentById = async (id) => {
  try {
    const response = await api.get(`/api/documents/${id}`);
    return response.data;
  } catch (error) {
    console.error("API getDocumentById error:", error);
    throw error;
  }
};