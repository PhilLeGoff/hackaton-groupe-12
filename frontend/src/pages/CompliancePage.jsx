import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ErrorAlert } from "../components/ErrorAlert";
const fallbackGlobalChecks = [];
const fallbackRequiredDocuments = [];
const fallbackComplianceAnomalies = [];
const fallbackDecisionHistory = [];
import { getComplianceByCaseId, updateCompliance } from "../api/compliance";
import { getAutofill } from "../api/cases";

const getCheckVariant = (passed) => (passed ? "success" : "danger");

const getDocClasses = (type) => {
  switch (type) {
    case "success":
      return "bg-emerald-50 border-emerald-200 text-emerald-800";
    case "danger":
      return "bg-rose-50 border-rose-200 text-rose-800";
    case "warning":
      return "bg-amber-50 border-amber-200 text-amber-800";
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
      : Array.isArray(data?.complianceAnomalies)
      ? data.complianceAnomalies
      : fallbackComplianceAnomalies,
    decisionHistory: Array.isArray(data?.decisionHistory)
      ? data.decisionHistory
      : Array.isArray(data?.history)
      ? data.history
      : fallbackDecisionHistory,
    dossierName: data?.companyName || data?.company_name || "Société Alpha",
    updatedAt: data?.updatedAt || data?.updated_at || "Aujourd'hui à 14:02",
    currentStatus: data?.status || "À revoir",
    complianceId: data?.id || data?._id || null,
  };
};

const fallbackComplianceData = {
  globalChecks: fallbackGlobalChecks,
  requiredDocuments: fallbackRequiredDocuments,
  anomalies: fallbackComplianceAnomalies,
  decisionHistory: fallbackDecisionHistory,
  dossierName: "Société Alpha",
  updatedAt: "Aujourd'hui à 14:02",
  currentStatus: "À revoir",
  complianceId: null,
};

export const CompliancePage = () => {
  const { caseId } = useParams();

  const [complianceData, setComplianceData] = useState(fallbackComplianceData);
  const [autofillData, setAutofillData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState("");

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        setError("");

        const [complianceResult, autofillResult] = await Promise.allSettled([
          getComplianceByCaseId(caseId),
          getAutofill(caseId),
        ]);

        if (complianceResult.status === "fulfilled" && complianceResult.value) {
          setComplianceData(normalizeCompliance(complianceResult.value));
        }

        if (autofillResult.status === "fulfilled" && autofillResult.value) {
          setAutofillData(autofillResult.value);

          const af = autofillResult.value;
          if (af.compliance) {
            setComplianceData((prev) => {
              const checks = [];
              if (af.compliance.urssaf_valid !== undefined) {
                checks.push({ label: "Attestation URSSAF valide", passed: af.compliance.urssaf_valid });
              }
              if (af.compliance.kbis_present !== undefined) {
                checks.push({ label: "KBIS présent", passed: af.compliance.kbis_present });
              }
              if (af.compliance.rib_present !== undefined) {
                checks.push({ label: "RIB présent", passed: af.compliance.rib_present });
              }
              if (af.compliance.all_sirets_match !== undefined) {
                checks.push({ label: "SIRET cohérent sur les pièces", passed: af.compliance.all_sirets_match });
              }

              const crossAnomalies = af.compliance.anomalies?.map((a) => ({
                title: a.field || "Anomalie inter-documents",
                description: a.message || "",
                level: a.level || "warning",
              })) || [];

              return {
                ...prev,
                globalChecks: checks.length > 0 ? checks : prev.globalChecks,
                anomalies: crossAnomalies.length > 0 ? crossAnomalies : prev.anomalies,
                dossierName: af.company_name || prev.dossierName,
              };
            });
          }
        }

        if (complianceResult.status === "rejected" && autofillResult.status === "rejected") {
          setError("API indisponible, affichage des données de démonstration.");
          setComplianceData(fallbackComplianceData);
        }
      } catch (err) {
        console.error("Erreur chargement conformité:", err);
        setError(
          "Impossible de charger la conformité depuis l'API. Affichage des données de démonstration.",
        );
        setComplianceData(fallbackComplianceData);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [caseId]);

  const handleDecision = async (decision) => {
    if (!complianceData.complianceId) {
      setError("Impossible de mettre à jour : ID de conformité manquant.");
      return;
    }
    try {
      setActionLoading(decision);
      await updateCompliance(complianceData.complianceId, decision);
      setComplianceData((prev) => ({
        ...prev,
        currentStatus: decision === "approved" ? "Conforme" : decision === "rejected" ? "Rejeté" : "À revoir",
      }));
    } catch (err) {
      console.error("Erreur décision:", err);
      setError("Impossible de mettre à jour la conformité.");
    } finally {
      setActionLoading("");
    }
  };

  const passedChecks = complianceData.globalChecks.filter((item) => item.passed).length;
  const failedChecks = complianceData.globalChecks.filter((item) => !item.passed).length;
  const complianceScore =
    complianceData.globalChecks.length > 0
      ? Math.round((passedChecks / complianceData.globalChecks.length) * 100)
      : 0;

  const getScoreVariant = () => {
    if (complianceScore >= 80) return "success";
    if (complianceScore >= 50) return "warning";
    return "danger";
  };

  const getStatusColor = () => {
    const status = complianceData.currentStatus.toLowerCase();
    if (status === "conforme" || status === "approved") return "bg-emerald-100 text-emerald-800 border-emerald-200";
    if (status === "rejeté" || status === "rejected") return "bg-rose-100 text-rose-800 border-rose-200";
    return "bg-amber-100 text-amber-800 border-amber-200";
  };

  return (
    <Layout
      title={`Conformité du dossier #${caseId}`}
      subtitle="Vérifie les pièces obligatoires, analyse les incohérences et prends une décision finale sur la conformité du dossier."
    >
      <div className="space-y-8">
        {error && <ErrorAlert message={error} />}

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
                badge={getScoreVariant() === "success" ? "OK" : "Attention"}
                badgeVariant={getScoreVariant()}
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

            {autofillData && (
              <SectionCard
                title="Informations pré-remplies"
                subtitle="Données agrégées automatiquement depuis les documents du dossier."
              >
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  {autofillData.company_name && (
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">Raison sociale</p>
                      <p className="mt-1 font-semibold text-slate-900">{autofillData.company_name}</p>
                    </div>
                  )}
                  {autofillData.siret && (
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">SIRET</p>
                      <p className="mt-1 font-semibold text-slate-900">{autofillData.siret}</p>
                    </div>
                  )}
                  {autofillData.vat && (
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">TVA</p>
                      <p className="mt-1 font-semibold text-slate-900">{autofillData.vat}</p>
                    </div>
                  )}
                  {autofillData.compliance?.iban && (
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">IBAN</p>
                      <p className="mt-1 font-semibold text-slate-900">{autofillData.compliance.iban}</p>
                    </div>
                  )}
                </div>

                {autofillData.compliance?.urssaf_expiry && (
                  <div className="mt-4 rounded-2xl bg-slate-50 p-4">
                    <p className="text-sm text-slate-500">Expiration URSSAF</p>
                    <p className={`mt-1 font-semibold ${autofillData.compliance.urssaf_valid ? "text-emerald-700" : "text-rose-700"}`}>
                      {autofillData.compliance.urssaf_expiry}
                      {autofillData.compliance.urssaf_valid ? " (Valide)" : " (Expirée)"}
                    </p>
                  </div>
                )}
              </SectionCard>
            )}

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Checklist conformité"
                subtitle="Résultat détaillé des contrôles réglementaires et documentaires."
                rightElement={
                  <StatusBadge
                    label={complianceScore === 100 ? "Conforme" : "Validation partielle"}
                    variant={complianceScore === 100 ? "success" : "warning"}
                  />
                }
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
                <div className={`rounded-2xl border p-4 text-sm leading-6 ${getStatusColor()}`}>
                  {complianceScore === 100
                    ? "Tous les contrôles sont validés. Le dossier peut être marqué comme conforme."
                    : failedChecks > 0
                    ? "Le dossier ne peut pas être marqué comme conforme en l'état. Des pièces sont manquantes ou des incohérences ont été détectées."
                    : "Le dossier est en cours de vérification."}
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
                  <button
                    onClick={() => handleDecision("approved")}
                    disabled={!!actionLoading}
                    className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {actionLoading === "approved" ? "Validation..." : "Valider le dossier"}
                  </button>
                  <button
                    onClick={() => handleDecision("rejected")}
                    disabled={!!actionLoading}
                    className="rounded-2xl bg-rose-600 px-4 py-3 text-sm font-semibold text-white hover:bg-rose-700 disabled:opacity-50"
                  >
                    {actionLoading === "rejected" ? "Rejet..." : "Rejeter le dossier"}
                  </button>
                  <button
                    onClick={() => handleDecision("review")}
                    disabled={!!actionLoading}
                    className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50"
                  >
                    {actionLoading === "review" ? "En cours..." : "Marquer à revoir"}
                  </button>
                  <Link
                    to={`/crm/${caseId}`}
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
                  <button
                    onClick={() => {
                      const report = {
                        caseId,
                        dossierName: complianceData.dossierName,
                        currentStatus: complianceData.currentStatus,
                        complianceScore,
                        globalChecks: complianceData.globalChecks,
                        requiredDocuments: complianceData.requiredDocuments,
                        anomalies: complianceData.anomalies,
                        autofill: autofillData || null,
                        exportedAt: new Date().toISOString(),
                      };
                      const json = JSON.stringify(report, null, 2);
                      const blob = new Blob([json], { type: "application/json" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `compliance-report-${caseId}.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
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
