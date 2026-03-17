import React, { useState, useRef } from "react";
import { Layout } from "../components/Layout";
import { api } from "../api/axios";

export const UploadPage = () => {
  const [file, setFile] = useState(null);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const inputRef = useRef(null);

  const handleFileSelect = (selectedFile) => {
    setFile(selectedFile);
    setUploadResult(null);
    setErrorMessage("");
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      handleFileSelect(selectedFile);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFileSelect(droppedFile);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const openFileExplorer = () => {
    inputRef.current.click();
  };

  const handleUpload = async () => {
    if (!file) {
      setErrorMessage("Veuillez choisir un fichier.");
      return;
    }

    setIsUploading(true);
    setErrorMessage("");
    setUploadResult(null);

    const formData = new FormData();
    formData.append("files", file);

    try {
      const response = await api.post("/api/upload", formData);
      setUploadResult(response.data);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || "Impossible de contacter le backend.");
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Layout title="Upload de documents">
      <div className="flex flex-col items-center gap-6">
        <div
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onClick={openFileExplorer}
          className="border-2 border-dashed border-gray-500 p-10 rounded-lg text-center w-[420px] cursor-pointer"
        >
          <p className="text-lg mb-2">Glissez votre document ici</p>

          <p className="text-sm text-gray-400">
            ou cliquez pour choisir un fichier
          </p>

          <p className="text-xs text-gray-500 mt-2">
            Formats acceptés : PDF, JPEG, JPG
          </p>

          <button
            onClick={(e) => {
              e.stopPropagation();
              openFileExplorer();
            }}
            className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Choisir un fichier
          </button>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.jpeg,.jpg"
            onChange={handleFileChange}
            hidden
          />
        </div>

        {file && (
          <p className="text-green-400">
            Fichier sélectionné : {file.name}
          </p>
        )}

        {errorMessage && <p className="text-red-400">{errorMessage}</p>}

        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-6 py-2 rounded"
        >
          {isUploading ? "Upload en cours..." : "Upload"}
        </button>

        {uploadResult?.files && (
          <div className="mt-4 border border-gray-600 rounded-lg p-4 w-[420px] bg-gray-900 text-white">
            <h2 className="text-xl font-semibold mb-3">
              Résultat de l'upload
            </h2>
            {uploadResult.files.map((f, i) => (
              <div key={i} className="mb-2">
                <p><strong>Nom :</strong> {f.filename}</p>
                <p><strong>Statut :</strong> {f.status === "duplicate" ? "Doublon détecté" : "Uploadé"}</p>
                {f.message && <p className="text-yellow-400 text-sm">{f.message}</p>}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};