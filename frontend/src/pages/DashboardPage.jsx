import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { getDocuments } from "../api/documents";

const getStatusVariant = (status) => {
  switch (status) {
    case "completed":
      return "success";
    case "error":
      return "danger";
    case "processing":
      return "info";
    default:
      return "warning";
  }
};

const getStatusLabel = (status) => {
  switch (status) {
    case "completed":
      return "Terminé";
    case "error":
      return "Erreur";
    case "processing":
      return "En cours";
    case "uploaded":
      return "En attente";
    default:
      return status;
  }
};

export const DashboardPage = () => {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDocuments = async () => {
      try {
        setLoading(true);
        setError("");
        const data = await getDocuments();
        setDocuments(data);
      } catch (err) {
        console.error("Erreur chargement documents:", err);
        setError("API indisponible.");
      } finally {
        setLoading(false);
      }
    };
    fetchDocuments();
  }, []);

  const totalDocuments = documents.length;
  const completedDocs = documents.filter((d) => d.status === "completed").length;
  const pendingDocs = documents.filter((d) => d.status !== "completed" && d.status !== "error").length;
  const errorDocs = documents.filter((d) => d.status === "error").length;

  return (
    <Layout
      title="Dashboard"
      subtitle="Vue d'ensemble des documents uploadés et de leur état de traitement par la pipeline IA."
    >
      <div className="space-y-8">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Documents totaux"
            value={totalDocuments}
            subtitle="Nombre total de documents uploadés."
            badge="Global"
          />
          <StatCard
            title="Analyses terminées"
            value={completedDocs}
            subtitle="Documents traités avec succès par la pipeline."
            badge="OK"
            badgeVariant="success"
          />
          <StatCard
            title="En attente"
            value={pendingDocs}
            subtitle="Documents en cours de traitement ou en file."
            badge="En cours"
            badgeVariant="warning"
          />
          <StatCard
            title="Erreurs"
            value={errorDocs}
            subtitle="Documents dont le traitement a échoué."
            badge="Alerte"
            badgeVariant="danger"
          />
        </section>

        {error && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        <SectionCard
          title="Historique des documents"
          subtitle="Liste complète des fichiers uploadés et leur progression dans la pipeline."
          rightElement={
            <Link
              to="/upload"
              className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
            >
              + Upload
            </Link>
          }
          className="overflow-hidden p-0"
        >
          {loading ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Chargement des documents...
            </div>
          ) : documents.length === 0 ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Aucun document.{" "}
              <Link to="/upload" className="font-semibold text-slate-900 hover:underline">
                Uploader un fichier
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead className="bg-slate-50">
                  <tr className="text-left text-sm text-slate-500">
                    <th className="px-6 py-4 font-medium">Document</th>
                    <th className="px-6 py-4 font-medium">Type</th>
                    <th className="px-6 py-4 font-medium">Confiance</th>
                    <th className="px-6 py-4 font-medium">Statut</th>
                    <th className="px-6 py-4 font-medium text-right">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.map((doc) => (
                    <tr
                      key={doc.id}
                      className="border-t border-slate-100 transition hover:bg-slate-50/70"
                    >
                      <td className="px-6 py-5">
                        <div>
                          <p className="font-semibold text-slate-900">{doc.name}</p>
                          <p className="mt-1 text-sm text-slate-500">ID: {doc.id.slice(0, 8)}...</p>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-sm text-slate-700">
                        {doc.type || "Non classifié"}
                      </td>
                      <td className="px-6 py-5 text-sm font-semibold text-slate-900">
                        {doc.confidence}
                      </td>
                      <td className="px-6 py-5">
                        <StatusBadge
                          label={getStatusLabel(doc.status)}
                          variant={getStatusVariant(doc.status)}
                        />
                      </td>
                      <td className="px-6 py-5 text-right">
                        <Link
                          to={`/documents/${doc.id}`}
                          className="inline-flex items-center rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                        >
                          Voir détail
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </Layout>
  );
};
