import React, { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { api } from "../api/axios";

const getStatusInfo = (status) => {
  switch (status) {
    case "uploaded":
      return { label: "En attente", style: "border-blue-200 bg-blue-50", done: false };
    case "processing":
      return { label: "Analyse en cours...", style: "border-amber-200 bg-amber-50", done: false };
    case "completed":
    case "Analyse terminee":
      return { label: "Terminé", style: "border-emerald-200 bg-emerald-50", done: true };
    case "validated":
      return { label: "Validé", style: "border-emerald-200 bg-emerald-50", done: true };
    case "A verifier":
    case "to_review":
      return { label: "À vérifier", style: "border-amber-200 bg-amber-50", done: true };
    case "error":
      return { label: "Erreur", style: "border-red-200 bg-red-50", done: true };
    default:
      return { label: status, style: "border-slate-100 bg-slate-50", done: false };
  }
};

export const UploadPage = () => {
  const [files, setFiles] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const intervalRef = useRef(null);
  const inputRef = useRef(null);

  // Poll document statuses after upload
  useEffect(() => {
    if (!uploadedFiles) return;

    const poll = async () => {
      try {
        const updated = await Promise.all(
          uploadedFiles.map(async (f) => {
            if (!f.id) return f;
            try {
              const resp = await api.get(`/api/documents/${f.id}`);
              return { ...f, status: resp.data.status, type: resp.data.type };
            } catch {
              return f;
            }
          })
        );
        setUploadedFiles(updated);

        const allDone = updated.every((f) => getStatusInfo(f.status).done);
        if (allDone && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch {
        // ignore
      }
    };

    intervalRef.current = setInterval(poll, 5000);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [uploadedFiles?.length]);

  const handleFilesSelect = (selectedFiles) => {
    const filesArray = Array.from(selectedFiles).slice(0, 3);
    setFiles(filesArray);
    setUploadedFiles(null);
    setErrorMessage("");
  };

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) handleFilesSelect(e.target.files);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length > 0) handleFilesSelect(e.dataTransfer.files);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setIsUploading(true);
    setErrorMessage("");
    setUploadedFiles(null);

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    try {
      const response = await api.post("/api/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const result = (response.data.files || []).map((f) => ({
        ...f,
        status: "uploaded",
      }));
      setUploadedFiles(result);
      setFiles([]);
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail || "Impossible de contacter le backend."
      );
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const pendingCount = uploadedFiles
    ? uploadedFiles.filter((f) => !getStatusInfo(f.status).done).length
    : 0;
  const allDone = uploadedFiles && pendingCount === 0;

  return (
    <Layout title="Dépôt de documents" subtitle="Déposez vos fichiers pour lancer l'extraction IA automatique.">
      <div className="mx-auto max-w-xl space-y-6">

        {/* Drop zone */}
        <button
          type="button"
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current.click()}
          className="flex w-full cursor-pointer flex-col items-center rounded-3xl border-2 border-dashed border-slate-300 bg-white p-10 text-center transition hover:border-slate-400 hover:bg-slate-50"
        >
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-2xl">+</div>
          <p className="mt-4 text-base font-semibold text-slate-900">Glissez vos documents ici</p>
          <p className="mt-1 text-sm text-slate-500">ou cliquez pour parcourir vos fichiers</p>
          <p className="mt-3 text-xs text-slate-400">PDF, DOCX, JPEG, PNG, TXT — max 20 Mo — 3 fichiers max</p>
          <input ref={inputRef} type="file" accept=".pdf,.docx,.jpeg,.jpg,.png,.txt" onChange={handleFileChange} multiple hidden />
        </button>

        {/* Selected files */}
        {files.length > 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-semibold text-slate-900">
              {files.length} fichier{files.length > 1 ? "s" : ""} prêt{files.length > 1 ? "s" : ""}
            </p>
            <ul className="mt-2 space-y-1">
              {files.map((file, i) => (
                <li key={i} className="flex items-center justify-between text-sm text-slate-600">
                  <span>{file.name}</span>
                  <span className="text-xs text-slate-400">{(file.size / 1024 / 1024).toFixed(1)} Mo</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {errorMessage && (
          <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">{errorMessage}</div>
        )}

        {/* Upload button */}
        {!uploadedFiles && (
          <button
            onClick={handleUpload}
            disabled={isUploading || files.length === 0}
            className="w-full rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {isUploading ? "Envoi en cours..." : "Lancer l'upload"}
          </button>
        )}

        {/* Upload results with live status */}
        {uploadedFiles && (
          <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                {allDone ? "Tous les fichiers sont prêts" : "Analyse en cours"}
              </h2>
              {!allDone && (
                <span className="inline-flex items-center gap-2 text-xs font-medium text-amber-600">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-amber-500" />
                  {pendingCount}/{uploadedFiles.length}
                </span>
              )}
            </div>

            {!allDone && (
              <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-slate-900 transition-all duration-500"
                  style={{ width: `${((uploadedFiles.length - pendingCount) / uploadedFiles.length) * 100}%` }}
                />
              </div>
            )}

            <div className="mt-4 space-y-3">
              {uploadedFiles.map((file, i) => {
                const info = getStatusInfo(file.status);
                return (
                  <div key={i} className={`flex items-center justify-between rounded-2xl border p-4 ${info.style}`}>
                    <div>
                      <p className="text-sm font-medium text-slate-900">{file.filename}</p>
                      <p className="text-xs text-slate-600">
                        {info.label}
                        {info.done && file.type ? ` — ${file.type}` : ""}
                      </p>
                    </div>
                    {info.done && file.id ? (
                      <Link
                        to={`/documents/${file.id}`}
                        className="rounded-xl bg-slate-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-slate-800"
                      >
                        Voir
                      </Link>
                    ) : !info.done ? (
                      <div className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-slate-700" />
                    ) : null}
                  </div>
                );
              })}
            </div>

            {allDone && (
              <Link
                to="/dashboard"
                className="mt-4 inline-flex w-full justify-center rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800"
              >
                Voir le suivi
              </Link>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
};
