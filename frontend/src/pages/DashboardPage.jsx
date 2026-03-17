import React from "react";
import { Layout } from "../components/Layout";

// Dashboard affichant un aperçu des documents analysés
// (version mock en attendant la connexion avec le backend)
export const DashboardPage = () => {
  const documents = [
    {
      name: "facture_001.pdf",
      type: "Facture",
      size: "93 734 octets",
      status: "Analyse terminée",
    },
    {
      name: "devis_client.jpg",
      type: "Devis",
      size: "45 120 octets",
      status: "Analyse terminée",
    },
    {
      name: "attestation.jpeg",
      type: "Attestation",
      size: "28 540 octets",
      status: "En attente",
    },
  ];

  const totalDocuments = documents.length;
  const analysedDocuments = documents.filter(
    (doc) => doc.status === "Analyse terminée"
  ).length;
  const pendingDocuments = documents.filter(
    (doc) => doc.status === "En attente"
  ).length;

  return (
    <Layout title="Dashboard" className="items-stretch">
      <div className="w-full max-w-5xl mx-auto flex flex-col gap-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">Documents uploadés</p>
            <h2 className="text-3xl font-bold mt-2">{totalDocuments}</h2>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">Analyses terminées</p>
            <h2 className="text-3xl font-bold mt-2">{analysedDocuments}</h2>
          </div>

          <div className="bg-gray-900 border border-gray-700 rounded-lg p-5">
            <p className="text-gray-400 text-sm">En attente</p>
            <h2 className="text-3xl font-bold mt-2">{pendingDocuments}</h2>
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-700 rounded-lg p-6">
          <h2 className="text-2xl font-semibold mb-4">
            Historique des documents
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b border-gray-700 text-left">
                  <th className="p-3">Nom du document</th>
                  <th className="p-3">Type</th>
                  <th className="p-3">Taille</th>
                  <th className="p-3">Statut</th>
                </tr>
              </thead>

              <tbody>
                {documents.map((doc, index) => (
                  <tr
                    key={index}
                    className="border-b border-gray-800 hover:bg-gray-800 transition"
                  >
                    <td className="p-3">{doc.name}</td>
                    <td className="p-3">{doc.type}</td>
                    <td className="p-3">{doc.size}</td>
                    <td className="p-3">
                      <span
                        className={`px-3 py-1 rounded-full text-sm ${
                          doc.status === "Analyse terminée"
                            ? "bg-green-900 text-green-300"
                            : "bg-yellow-900 text-yellow-300"
                        }`}
                      >
                        {doc.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </Layout>
  );
};