import React, { useState, useRef } from "react";
import { Layout } from "../components/Layout";

export const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [uploadResult, setUploadResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);

  const inputRef = useRef(null);

  const handleFilesSelect = (selectedFiles) => {
    const filesArray = Array.from(selectedFiles).slice(0, 3);
    setFiles(filesArray);
    setUploadResult(null);
    setErrorMessage("");
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      handleFilesSelect(e.target.files);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) {
      handleFilesSelect(e.dataTransfer.files);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const openFileExplorer = () => {
    inputRef.current.click();
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      setErrorMessage("Veuillez choisir au moins un fichier.");
      return;
    }

    setIsUploading(true);
    setErrorMessage("");
    setUploadResult(null);

    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });

    try {
      const response = await fetch("http://127.0.0.1:8000/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        setErrorMessage(data.detail || "Erreur lors de l'upload.");
        return;
      }

      setUploadResult(data);
    } catch (error) {
      setErrorMessage("Impossible de contacter le backend.");
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
          <p className="text-lg mb-2">Glissez vos documents ici</p>

          <p className="text-sm text-gray-400">
            ou cliquez pour choisir un ou plusieurs fichiers
          </p>

          <p className="text-xs text-gray-500 mt-2">
            Formats acceptés : PDF, DOCX, JPEG, JPG, PNG, TXT
          </p>

          <p className="text-xs text-gray-500 mt-1">
            Maximum : 3 fichiers
          </p>

          <button
            onClick={(e) => {
              e.stopPropagation();
              openFileExplorer();
            }}
            className="mt-4 bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
          >
            Choisir des fichiers
          </button>

          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx,.jpeg,.jpg,.png,.txt"
            onChange={handleFileChange}
            multiple
            hidden
          />
        </div>

        {files.length > 0 && (
          <div className="text-green-400 text-sm">
            <p className="mb-2 font-semibold">Fichiers sélectionnés :</p>
            <ul className="list-disc list-inside">
              {files.map((file, index) => (
                <li key={index}>{file.name}</li>
              ))}
            </ul>
          </div>
        )}

        {errorMessage && <p className="text-red-400">{errorMessage}</p>}

        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-500 text-white px-6 py-2 rounded"
        >
          {isUploading ? "Upload en cours..." : "Upload"}
        </button>

        {uploadResult && (
          <div className="mt-4 border border-gray-600 rounded-lg p-4 w-[420px] bg-gray-900 text-white">
            <h2 className="text-xl font-semibold mb-3">
              Résultat de l'upload
            </h2>

            {uploadResult.files?.map((file, index) => (
              <div key={index} className="mb-3 border-b border-gray-700 pb-2 last:border-b-0">
                <p>
                  <strong>Nom :</strong> {file.filename}
                </p>
                <p>
                  <strong>Statut :</strong> {file.status}
                </p>
                {file.message && (
                  <p>
                    <strong>Message :</strong> {file.message}
                  </p>
                )}
                {file.id && (
                  <p>
                    <strong>ID :</strong> {file.id}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
};