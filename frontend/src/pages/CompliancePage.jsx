import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import {
  globalChecks as fallbackGlobalChecks,
  requiredDocuments as fallbackRequiredDocuments,
  complianceAnomalies as fallbackComplianceAnomalies,
  decisionHistory as fallbackDecisionHistory,
} from "../data/mockCompliance";
import { getComplianceByCaseId } from "../api/compliance";

const getCheckVariant = (passed) => (passed ? "success" : "danger");

const getDocClasses = (type) => {
  switch (type) {
    case "success":
      return "bg-emerald-50 border-emerald-200 text-emerald-800";
    case "danger":
      return "bg-rose-50 border-rose-200 text-rose-800";
    default:
      return "bg-slate-50 border-slate-200 text-slate-800";
  }
};

const getAnomalyClasses = (level) => {
  switch (level) {
    case "danger":
      return "bg-rose-50 border-rose-200 text-rose-800";
    case "warning":
      return "bg-amber-50 border-amber-200 text-amber-800";
    default:
      return "bg-sky-50 border-sky-200 text-sky-800";
  }
};

const normalizeCompliance = (data) => {
  return {
    globalChecks: Array.isArray(data?.globalChecks)
      ? data.globalChecks
      : Array.isArray(data?.checks)
      ? data.checks
      : fallbackGlobalChecks,
    requiredDocuments: Array.isArray(data?.requiredDocuments)
      ? data.requiredDocuments
      : Array.isArray(data?.documents)
      ? data.documents
      : fallbackRequiredDocuments,
    anomalies: Array.isArray(data?.anomalies)
      ? data.anomalies
      : fallbackComplianceAnomalies,
    decisionHistory: Array.isArray(data?.decisionHistory)
      ? data.decisionHistory
      : Array.isArray(data?.history)
      ? data.history
      : fallbackDecisionHistory,
    dossierName: data?.companyName || data?.company_name || "Société Alpha",
    updatedAt: data?.updatedAt || data?.updated_at || "Aujourd’hui à 14:02",
    currentStatus: data?.status || "À revoir",
  };
};

export const CompliancePage = () => {
  const { caseId } = useParams();

  const [complianceData, setComplianceData] = useState({
    globalChecks: fallbackGlobalChecks,
    requiredDocuments: fallbackRequiredDocuments,
    anomalies: fallbackComplianceAnomalies,
    decisionHistory: fallbackDecisionHistory,
    dossierName: "Société Alpha",
    updatedAt: "Aujourd’hui à 14:02",
    currentStatus: "À revoir",
  });

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadCompliance = async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getComplianceByCaseId(caseId);

        if (data && typeof data === "object") {
          setComplianceData(normalizeCompliance(data));
        } else {
          setComplianceData({
            globalChecks: fallbackGlobalChecks,
            requiredDocuments: fallbackRequiredDocuments,
            anomalies: fallbackComplianceAnomalies,
            decisionHistory: fallbackDecisionHistory,
            dossierName: "Société Alpha",
            updatedAt: "Aujourd’hui à 14:02",
            currentStatus: "À revoir",
          });
        }
      } catch (err) {
        console.error("Erreur chargement conformité:", err);
        setError("API indisponible, affichage des données de démonstration.");
        setComplianceData({
          globalChecks: fallbackGlobalChecks,
          requiredDocuments: fallbackRequiredDocuments,
          anomalies: fallbackComplianceAnomalies,
          decisionHistory: fallbackDecisionHistory,
          dossierName: "Société Alpha",
          updatedAt: "Aujourd’hui à 14:02",
          currentStatus: "À revoir",
        });
      } finally {
        setLoading(false);
      }
    };

    loadCompliance();
  }, [caseId]);

  const passedChecks = complianceData.globalChecks.filter((item) => item.passed).length;
  const failedChecks = complianceData.globalChecks.filter((item) => !item.passed).length;
  const complianceScore =
    complianceData.globalChecks.length > 0
      ? Math.round((passedChecks / complianceData.globalChecks.length) * 100)
      : 0;

  return (
    <Layout
      title={`Conformité du dossier #${caseId}`}
      subtitle="Vérifie les pièces obligatoires, analyse les incohérences et prends une décision finale sur la conformité du dossier."
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
              Chargement de la conformité...
            </div>
          </SectionCard>
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StatCard
                title="Score conformité"
                value={`${complianceScore}%`}
                subtitle="Évaluation globale du dossier"
              />
              <StatCard
                title="Contrôles validés"
                value={passedChecks}
                subtitle="Règles satisfaites"
                badge="OK"
                badgeVariant="success"
              />
              <StatCard
                title="Échecs détectés"
                value={failedChecks}
                subtitle="Points de blocage identifiés"
                badge="Alerte"
                badgeVariant="danger"
              />
              <StatCard
                title="Décision suggérée"
                value={complianceData.currentStatus}
                subtitle="Validation humaine recommandée"
                badge="Revue"
                badgeVariant="warning"
              />
            </section>

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Checklist conformité"
                subtitle="Résultat détaillé des contrôles réglementaires et documentaires."
                rightElement={<StatusBadge label="Validation partielle" variant="warning" />}
                className="xl:col-span-2"
              >
                <div className="grid gap-4 md:grid-cols-2">
                  {complianceData.globalChecks.map((check, index) => (
                    <div
                      key={`${check.label}-${index}`}
                      className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4"
                    >
                      <span className="font-medium text-slate-800">{check.label}</span>
                      <StatusBadge
                        label={check.passed ? "OK" : "Échec"}
                        variant={getCheckVariant(check.passed)}
                      />
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard title="Résumé décisionnel">
                <div className="rounded-2xl bg-amber-50 p-4 text-sm leading-6 text-amber-800">
                  Le dossier ne peut pas être marqué comme conforme en l’état. Une pièce obligatoire
                  manque et au moins un document doit être revu manuellement.
                </div>

                <div className="mt-5 space-y-4">
                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Statut actuel</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {complianceData.currentStatus}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Dossier</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {complianceData.dossierName}
                    </p>
                  </div>

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Dernier contrôle</p>
                    <p className="mt-1 font-semibold text-slate-900">
                      {complianceData.updatedAt}
                    </p>
                  </div>
                </div>

                <div className="mt-6 flex flex-col gap-3">
                  <button className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700">
                    Valider le dossier
                  </button>
                  <button className="rounded-2xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white hover:bg-rose-700">
                    Rejeter le dossier
                  </button>
                  <button className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-semibold text-white hover:bg-amber-600">
                    Marquer à revoir
                  </button>
                  <Link
                    to="/crm/1"
                    className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-50"
                  >
                    Retour au dossier
                  </Link>
                </div>
              </SectionCard>
            </section>

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Pièces requises"
                subtitle="Vérification de présence des documents attendus dans le dossier."
                rightElement={
                  <button className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                    Exporter rapport
                  </button>
                }
                className="xl:col-span-2"
              >
                <div className="grid gap-4 md:grid-cols-2">
                  {complianceData.requiredDocuments.map((doc, index) => (
                    <div
                      key={`${doc.name}-${index}`}
                      className={`rounded-2xl border p-5 ${getDocClasses(doc.type)}`}
                    >
                      <p className="font-semibold">{doc.name}</p>
                      <p className="mt-2 text-sm">{doc.status}</p>
                    </div>
                  ))}
                </div>

                <div className="mt-6 rounded-2xl bg-slate-50 p-4 text-sm leading-6 text-slate-600">
                  Le système peut afficher ici, plus tard, les documents réellement fournis par le backend
                  et comparer automatiquement les pièces présentes avec la liste réglementaire attendue.
                </div>
              </SectionCard>

              <SectionCard
                title="Historique"
                subtitle="Suivi des étapes du contrôle de conformité."
              >
                <div className="space-y-4">
                  {complianceData.decisionHistory.map((item, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div
                          className={`h-3.5 w-3.5 rounded-full ${
                            item.status === "Terminé" ? "bg-emerald-500" : "bg-amber-500"
                          }`}
                        />
                        {index < complianceData.decisionHistory.length - 1 && (
                          <div className="mt-2 h-12 w-px bg-slate-200" />
                        )}
                      </div>

                      <div className="pb-3">
                        <p className="font-semibold text-slate-900">{item.action}</p>
                        <p className="mt-1 text-sm text-slate-500">{item.date}</p>
                        <p className="mt-1 text-sm text-slate-600">{item.status}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </SectionCard>
            </section>

            <SectionCard
              title="Anomalies détectées"
              subtitle="Analyse des incohérences ou insuffisances relevées pendant le contrôle."
              rightElement={
                <StatusBadge
                  label={`${complianceData.anomalies.length} alertes`}
                  variant="danger"
                />
              }
            >
              <div className="grid gap-4 lg:grid-cols-3">
                {complianceData.anomalies.map((item, index) => (
                  <div
                    key={`${item.title}-${index}`}
                    className={`rounded-2xl border p-5 ${getAnomalyClasses(item.level)}`}
                  >
                    <p className="font-semibold">{item.title}</p>
                    <p className="mt-2 text-sm leading-6">{item.description}</p>
                  </div>
                ))}
              </div>
            </SectionCard>
          </>
        )}
      </div>
    </Layout>
  );
};