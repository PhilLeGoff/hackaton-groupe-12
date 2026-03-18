import React, { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {api} from  "../api/axios"

export const DashboardPage = () => {
  const [documents, setDocuments] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        const response = await api.get("/documents");
        const data = await response.data;

        if (!response.ok) {
          setErrorMessage("Impossible de récupérer les documents.");
          return;
        }
        
        setDocuments(data);
      } catch (error) {
        setErrorMessage("Erreur de connexion avec le backend.");
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocuments();
  }, []);

  const totalDocuments = documents.length;
  const uploadedDocuments = documents.filter(
    (doc) => doc.status === "uploaded"
  ).length;
  const otherDocuments = totalDocuments - uploadedDocuments;

  return (
    <Layout title="Dashboard" className="items-stretch">
      <div className="w-full max-w-5xl mx-auto flex flex-col gap-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">Documents</p>
            <h2 className="text-3xl font-bold mt-2">{totalDocuments}</h2>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">Uploadés</p>
            <h2 className="text-3xl font-bold mt-2">{uploadedDocuments}</h2>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">Autres statuts</p>
            <h2 className="text-3xl font-bold mt-2">{otherDocuments}</h2>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">
            Historique des documents
          </h2>

          {isLoading && <p>Chargement des documents...</p>}
          {errorMessage && <p className="text-red-400">{errorMessage}</p>}

          {!isLoading && !errorMessage && (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b border-gray-700 text-left">
                    <th className="p-3">Nom</th>
                    <th className="p-3">Type</th>
                    <th className="p-3">Statut</th>
                    <th className="p-3">Confiance</th>
                  </tr>
                </thead>

                <tbody>
                  {documents.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-b border-gray-800 hover:bg-gray-800 transition"
                    >
                      <td className="p-3">{doc.name || "N/A"}</td>
                      <td className="p-3">{doc.type || "N/A"}</td>
                      <td className="p-3">{doc.status || "N/A"}</td>
                      <td className="p-3">{doc.confidence || "0%"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {documents.length === 0 && (
                <p className="mt-4 text-gray-400">
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