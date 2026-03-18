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

export const updateDocument = async (id, data) => {
  const response = await api.put(`/api/documents/${id}`, data);
  return response.data;
};

export const downloadDocument = async (id) => {
  const response = await api.get(`/api/documents/${id}/download`, {
    responseType: "blob",
  });
  return response.data;
};

export const uploadFiles = async (files) => {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  const response = await api.post("/api/upload", formData);
  return response.data;
};
