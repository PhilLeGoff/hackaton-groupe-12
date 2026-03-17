import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { caseSummary as fallbackCaseSummary } from "../data/mockCases";
import { mockDocuments } from "../data/mockDocuments";
import { getCaseById } from "../api/cases";

const getStatusVariant = (status) => {
  switch (status) {
    case "Analyse terminée":
      return "success";
    case "À vérifier":
    case "to_review":
      return "warning";
    case "Non conforme":
    case "non_compliant":
      return "danger";
    case "Conforme":
    case "compliant":
      return "success";
    default:
      return "default";
  }
};

const normalizeCase = (item) => ({
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  siret: item.siret || item.companySiret || "Non renseigné",
  status: item.status || "À vérifier",
  documents: item.documents ?? item.documentsCount ?? 0,
  contact: item.contact || item.email || "Non renseigné",
  sector: item.sector || item.activity || "Non renseigné",
  updatedAt: item.updatedAt || item.updated_at || "Récemment",
});

export const CaseDetailsPage = () => {
  const { caseId } = useParams();
  const [caseData, setCaseData] = useState(fallbackCaseSummary);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadCase = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getCaseById(caseId);

        if (data && typeof data === "object") {
          setCaseData(normalizeCase(data));
        } else {
          setCaseData(fallbackCaseSummary);
        }
      } catch (err) {
        console.error("Erreur chargement dossier:", err);
        setError("API indisponible, affichage des données de démonstration.");
        setCaseData(fallbackCaseSummary);
      } finally {
        setLoading(false);
      }
    };

    loadCase();
  }, [caseId]);

  return (
    <Layout
      title={`Détail du dossier #${caseId}`}
      subtitle="Consulte les informations du dossier, l’état des documents et accède rapidement aux modules d’analyse et de conformité."
    >
      <div className="space-y-8">
        {error && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {error}
          </div>
        )}

        {loading ? (
          <SectionCard title="Chargement">
            <div className="py-8 text-center text-slate-500">
              Chargement du dossier...
            </div>
          </SectionCard>
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StatCard
                title="Entreprise"
                value={caseData.companyName}
                subtitle={caseData.sector}
              />
              <StatCard
                title="SIRET"
                value={caseData.siret}
                subtitle="Identifiant entreprise"
              />
              <StatCard
                title="Statut"
                value={caseData.status}
                subtitle="Revue humaine requise"
                badge={caseData.status}
                badgeVariant={getStatusVariant(caseData.status)}
              />
              <StatCard
                title="Documents"
                value={caseData.documents}
                subtitle="Pièces associées au dossier"
              />
            </section>

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Informations dossier"
                rightElement={
                  <StatusBadge
                    label={caseData.status}
                    variant={getStatusVariant(caseData.status)}
                  />
                }
                className="xl:col-span-1"
              >
                <div className="space-y-4">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Entreprise</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {caseData.companyName}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">SIRET</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {caseData.siret}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Contact</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {caseData.contact}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Dernière mise à jour</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {caseData.updatedAt}
                    </p>
                  </div>
                </div>

                <div className="mt-6 grid gap-3">
                  <Link
                    to={`/compliance/${caseId}`}
                    className="inline-flex items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
                  >
                    Voir conformité
                  </Link>

                  <Link
                    to="/crm"
                    className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    Retour au CRM
                  </Link>
                </div>
              </SectionCard>

              <SectionCard
                title="Documents du dossier"
                subtitle="Liste des pièces analysées et état de traitement."
                rightElement={
                  <button className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white transition hover:bg-slate-800">
                    + Ajouter un document
                  </button>
                }
                className="xl:col-span-2"
              >
                <div className="space-y-4">
                  {mockDocuments.map((doc) => (
                    <div
                      key={doc.id}
                      className="group rounded-3xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white"
                    >
                      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <div className="flex items-start gap-4">
                          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white">
                            PDF
                          </div>

                          <div>
                            <p className="text-base font-semibold text-slate-900">
                              {doc.name}
                            </p>
                            <div className="mt-2 flex flex-wrap items-center gap-2">
                              <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700">
                                {doc.type}
                              </span>

                              <StatusBadge
                                label={doc.status}
                                variant={getStatusVariant(doc.status)}
                              />

                              <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
                                Confiance IA : {doc.confidence}
                              </span>
                            </div>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-3">
                          <Link
                            to={`/documents/${doc.id}`}
                            className="inline-flex items-center rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800"
                          >
                            Ouvrir
                          </Link>

                          <button className="inline-flex items-center rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50">
                            Télécharger
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </section>
          </>
        )}
      </div>
    </Layout>
  );
};