import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { mockCases } from "../data/mockCases";
import { getCases } from "../api/cases";

const getStatusVariant = (status) => {
  switch (status) {
    case "Conforme":
    case "compliant":
      return "success";
    case "Non conforme":
    case "non_compliant":
      return "danger";
    case "À vérifier":
    case "to_review":
      return "warning";
    default:
      return "default";
  }
};

const normalizeCase = (item) => ({
  id: item.id || item._id || "N/A",
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  siret: item.siret || item.companySiret || "Non renseigné",
  status: item.status || "À vérifier",
  documents: item.documents ?? item.documentsCount ?? 0,
  owner: item.owner || item.department || "Non assigné",
  updatedAt: item.updatedAt || item.updated_at || "Récemment",
});

export const CRMPage = () => {
  const [cases, setCases] = useState(mockCases);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const loadCases = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getCases();

        if (Array.isArray(data) && data.length > 0) {
          setCases(data.map(normalizeCase));
        } else {
          setCases(mockCases);
        }
      } catch (err) {
        console.error("Erreur chargement dossiers:", err);
        setError("API indisponible, affichage des données de démonstration.");
        setCases(mockCases);
      } finally {
        setLoading(false);
      }
    };

    loadCases();
  }, []);

  const filteredCases = useMemo(() => {
    const value = search.trim().toLowerCase();

    if (!value) return cases;

    return cases.filter((item) => {
      return (
        item.companyName.toLowerCase().includes(value) ||
        item.siret.toLowerCase().includes(value) ||
        item.status.toLowerCase().includes(value) ||
        item.owner.toLowerCase().includes(value)
      );
    });
  }, [cases, search]);

  const totalCases = filteredCases.length;
  const compliantCases = filteredCases.filter(
    (item) => item.status === "Conforme" || item.status === "compliant",
  ).length;
  const reviewCases = filteredCases.filter(
    (item) => item.status === "À vérifier" || item.status === "to_review",
  ).length;
  const nonCompliantCases = filteredCases.filter(
    (item) => item.status === "Non conforme" || item.status === "non_compliant",
  ).length;

  return (
    <Layout
      title="CRM documentaire"
      subtitle="Consulte les dossiers d’entreprise, suis l’état des documents analysés et accède rapidement aux modules de contrôle et de conformité."
    >
      <div className="space-y-8">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Dossiers totaux"
            value={totalCases}
            subtitle="Vue consolidée de tous les dossiers documentaires."
            badge="Global"
          />

          <StatCard
            title="Conformes"
            value={compliantCases}
            subtitle="Dossiers validés et prêts pour traitement final."
            badge="OK"
            badgeVariant="success"
          />

          <StatCard
            title="À vérifier"
            value={reviewCases}
            subtitle="Dossiers nécessitant une validation humaine."
            badge="Revue"
            badgeVariant="warning"
          />

          <StatCard
            title="Non conformes"
            value={nonCompliantCases}
            subtitle="Dossiers comportant des anomalies ou pièces manquantes."
            badge="Alerte"
            badgeVariant="danger"
          />
        </section>

        {error && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        <SectionCard>
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex w-full flex-col gap-3 md:flex-row">
              <div className="w-full md:max-w-md">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher une entreprise, un SIRET ou un statut..."
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white"
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <button className="rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white">
                  Tous
                </button>
                <button className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  Conforme
                </button>
                <button className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  À vérifier
                </button>
                <button className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                  Non conforme
                </button>
              </div>
            </div>

            <button className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800">
              + Nouveau dossier
            </button>
          </div>
        </SectionCard>

        <SectionCard
          title="Liste des dossiers"
          subtitle="Vue détaillée des entreprises, documents et statuts de conformité."
          rightElement={
            <div className="flex items-center gap-2">
              <button className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                Exporter
              </button>
              <button className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50">
                Actualiser
              </button>
            </div>
          }
          className="overflow-hidden p-0"
        >
          {loading ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Chargement des dossiers...
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Aucun dossier trouvé.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead className="bg-slate-50">
                  <tr className="text-left text-sm text-slate-500">
                    <th className="px-6 py-4 font-medium">Entreprise</th>
                    <th className="px-6 py-4 font-medium">SIRET</th>
                    <th className="px-6 py-4 font-medium">Équipe</th>
                    <th className="px-6 py-4 font-medium">Documents</th>
                    <th className="px-6 py-4 font-medium">Statut</th>
                    <th className="px-6 py-4 font-medium">Dernière mise à jour</th>
                    <th className="px-6 py-4 font-medium text-right">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredCases.map((item) => (
                    <tr
                      key={item.id}
                      className="border-t border-slate-100 transition hover:bg-slate-50/70"
                    >
                      <td className="px-6 py-5">
                        <div>
                          <p className="font-semibold text-slate-900">{item.companyName}</p>
                          <p className="mt-1 text-sm text-slate-500">Dossier #{item.id}</p>
                        </div>
                      </td>

                      <td className="px-6 py-5 text-sm text-slate-700">{item.siret}</td>

                      <td className="px-6 py-5">
                        <span className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-700">
                          {item.owner}
                        </span>
                      </td>

                      <td className="px-6 py-5 text-sm text-slate-700">
                        <span className="font-semibold text-slate-900">{item.documents}</span> pièces
                      </td>

                      <td className="px-6 py-5">
                        <StatusBadge
                          label={item.status}
                          variant={getStatusVariant(item.status)}
                        />
                      </td>

                      <td className="px-6 py-5 text-sm text-slate-500">{item.updatedAt}</td>

                      <td className="px-6 py-5 text-right">
                        <Link
                          to={`/crm/${item.id}`}
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

        <section className="grid gap-6 lg:grid-cols-3">
          <SectionCard
            title="Activité récente"
            rightElement={<span className="text-sm text-slate-500">Aujourd’hui</span>}
            className="lg:col-span-2"
          >
            <div className="space-y-4">
              <div className="flex items-start gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="mt-1 h-3 w-3 rounded-full bg-emerald-500" />
                <div>
                  <p className="font-medium text-slate-900">
                    Le dossier <span className="font-bold">Beta Services</span> a été validé.
                  </p>
                  <p className="mt-1 text-sm text-slate-500">Conformité confirmée • il y a 12 min</p>
                </div>
              </div>

              <div className="flex items-start gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="mt-1 h-3 w-3 rounded-full bg-amber-500" />
                <div>
                  <p className="font-medium text-slate-900">
                    Le dossier <span className="font-bold">Société Alpha</span> attend une revue.
                  </p>
                  <p className="mt-1 text-sm text-slate-500">Anomalie détectée sur le RIB • il y a 38 min</p>
                </div>
              </div>

              <div className="flex items-start gap-4 rounded-2xl bg-slate-50 p-4">
                <div className="mt-1 h-3 w-3 rounded-full bg-rose-500" />
                <div>
                  <p className="font-medium text-slate-900">
                    Le dossier <span className="font-bold">Gamma Industrie</span> a été rejeté.
                  </p>
                  <p className="mt-1 text-sm text-slate-500">
                    Pièce réglementaire manquante • il y a 1 h
                  </p>
                </div>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Aperçu rapide">
            <div className="space-y-4">
              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Taux de conformité</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">78%</p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Documents traités</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">20</p>
              </div>

              <div className="rounded-2xl bg-slate-50 p-4">
                <p className="text-sm text-slate-500">Dossiers en attente</p>
                <p className="mt-2 text-2xl font-bold text-slate-900">{reviewCases}</p>
              </div>
            </div>

            <Link
              to="/compliance/1"
              className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
            >
              Aller à la conformité
            </Link>
          </SectionCard>
        </section>
      </div>
    </Layout>
  );
};