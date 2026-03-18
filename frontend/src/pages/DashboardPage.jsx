import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { api } from "../api/axios";

const StatusBadge = ({ status }) => {
  const styles = {
    completed: "bg-emerald-50 text-emerald-700 border-emerald-200",
    "Analyse terminee": "bg-emerald-50 text-emerald-700 border-emerald-200",
    validated: "bg-emerald-50 text-emerald-700 border-emerald-200",
    uploaded: "bg-blue-50 text-blue-700 border-blue-200",
    processing: "bg-amber-50 text-amber-700 border-amber-200",
    to_review: "bg-amber-50 text-amber-700 border-amber-200",
    error: "bg-red-50 text-red-700 border-red-200",
  };
  return (
    <span className={`inline-flex rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles[status] || "bg-slate-50 text-slate-600 border-slate-200"}`}>
      {status || "N/A"}
    </span>
  );
};

export const DashboardPage = () => {
  const [documents, setDocuments] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    try {
      setIsLoading(true);
      setErrorMessage("");
      const response = await api.get("/api/documents?limit=100");
      const data = response.data;
      setDocuments(data.data || data);
    } catch (error) {
      setErrorMessage("Erreur de connexion avec le backend.");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
    const interval = setInterval(fetchDocuments, 10000);
    return () => clearInterval(interval);
  }, [fetchDocuments]);

  const totalDocuments = documents.length;
  const completedDocs = documents.filter(
    (doc) => doc.status === "completed" || doc.status === "Analyse terminee"
  ).length;
  const processingDocs = documents.filter(
    (doc) => doc.status === "processing" || doc.status === "uploaded"
  ).length;
  const errorDocs = documents.filter((doc) => doc.status === "error").length;

  const stats = [
    { label: "Total documents", value: totalDocuments, color: "bg-slate-900 text-white" },
    { label: "Traités", value: completedDocs, color: "bg-emerald-50 text-emerald-700 border border-emerald-200" },
    { label: "En cours", value: processingDocs, color: "bg-amber-50 text-amber-700 border border-amber-200" },
    { label: "Erreurs", value: errorDocs, color: "bg-red-50 text-red-700 border border-red-200" },
  ];

  return (
    <Layout title="Dashboard" subtitle="Suivi du pipeline de traitement des documents">
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className={`rounded-2xl p-5 ${stat.color}`}>
              <p className="text-sm font-medium opacity-80">{stat.label}</p>
              <p className="mt-1 text-3xl font-bold">{stat.value}</p>
            </div>
          ))}
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">
              Historique des documents
            </h2>
            <button
              onClick={fetchDocuments}
              disabled={isLoading}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              {isLoading ? "..." : "Rafraîchir"}
            </button>
          </div>

          {isLoading && (
            <p className="mt-4 text-sm text-slate-500">Chargement...</p>
          )}
          {errorMessage && (
            <p className="mt-4 text-sm text-red-600">{errorMessage}</p>
          )}

          {!isLoading && !errorMessage && (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 text-left">
                    <th className="pb-3 pr-4 font-medium text-slate-500">Nom</th>
                    <th className="pb-3 pr-4 font-medium text-slate-500">Type</th>
                    <th className="pb-3 pr-4 font-medium text-slate-500">Statut</th>
                    <th className="pb-3 pr-4 font-medium text-slate-500">Confiance</th>
                    <th className="pb-3 font-medium text-slate-500"></th>
                  </tr>
                </thead>

                <tbody>
                  {documents.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-slate-100 transition hover:bg-slate-50"
                    >
                      <td className="py-3 pr-4 font-medium text-slate-900">
                        {doc.name || "N/A"}
                      </td>
                      <td className="py-3 pr-4 text-slate-600">
                        {doc.type || "N/A"}
                      </td>
                      <td className="py-3 pr-4">
                        <StatusBadge status={doc.status} />
                      </td>
                      <td className="py-3 pr-4 text-slate-600">
                        {doc.confidence ? `${doc.confidence}%` : "—"}
                      </td>
                      <td className="py-3 text-right">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="text-sm font-medium text-slate-900 hover:text-slate-600"
                        >
                          Voir →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {documents.length === 0 && (
                <p className="mt-6 text-center text-sm text-slate-400">
                  Aucun document disponible pour le moment.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
};
