import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ErrorAlert } from "../components/ErrorAlert";
import {
  extractedFields as fallbackExtractedFields,
  documentAnomalies as fallbackDocumentAnomalies,
  timeline as fallbackTimeline,
} from "../data/mockDocuments";
import { getDocumentById, updateDocument, downloadDocument } from "../api/documents";
import { api } from "../api/axios";

const fallbackDocumentData = {
  type: "Facture",
  companyName: "Société Alpha",
  fileName: "facture_alpha.pdf",
  confidence: "94%",
  status: "À revoir",
  updatedAt: "Aujourd'hui à 14:00",
  caseId: null,
};

const normalizeDocument = (item) => ({
  id: item.id || item._id || "N/A",
  type: item.type || item.documentType || item.document_type || "Document",
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  fileName: item.fileName || item.filename || item.name || "document.pdf",
  confidence:
    item.confidence ||
    item.confidenceScore ||
    item.confidence_score ||
    "94%",
  status: item.status || item.analysisStatus || "À revoir",
  updatedAt: item.updatedAt || item.updated_at || "Aujourd'hui",
  caseId: item.caseId || item.case_id || null,
});

const normalizeExtractedFields = (data) => {
  if (Array.isArray(data?.extractedFields)) {
    return data.extractedFields.map((field) => ({
      label: field.label || field.name || "Champ",
      value: field.value ?? "Non renseigné",
      confidence: field.confidence || "90%",
    }));
  }
  return fallbackExtractedFields;
};

const normalizeAnomalies = (data) => {
  if (Array.isArray(data?.anomalies)) {
    return data.anomalies.map((item) => ({
      title: item.title || item.name || item.field || "Anomalie détectée",
      description: item.description || item.message || "Aucun détail fourni.",
      level: item.level || "warning",
    }));
  }
  return fallbackDocumentAnomalies;
};

const normalizeTimeline = (data) => {
  if (Array.isArray(data?.timeline)) {
    return data.timeline.map((item) => ({
      step: item.step || item.action || item.label || "Étape",
      status: item.status || "En attente",
      date: item.date || item.timestamp || "Non renseigné",
    }));
  }
  return fallbackTimeline;
};

const getConfidenceVariant = (confidence) => {
  const value = parseInt(confidence, 10);
  if (value >= 95) return "success";
  if (value >= 85) return "warning";
  return "danger";
};

const getFileType = (filename) => {
  const ext = (filename || "").split(".").pop().toLowerCase();
  if (ext === "pdf") return "pdf";
  if (["jpg", "jpeg", "png", "gif", "webp", "bmp"].includes(ext)) return "image";
  return "other";
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

export const DocumentDetailsPage = () => {
  const { documentId } = useParams();

  const [documentData, setDocumentData] = useState(fallbackDocumentData);
  const [fields, setFields] = useState(fallbackExtractedFields);
  const [anomalies, setAnomalies] = useState(fallbackDocumentAnomalies);
  const [timeline, setTimeline] = useState(fallbackTimeline);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionLoading, setActionLoading] = useState("");
  const [editMode, setEditMode] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [previewError, setPreviewError] = useState(false);

  useEffect(() => {
    const loadDocument = async () => {
      try {
        setLoading(true);
        setError("");

        const documentResponse = await getDocumentById(documentId);

        if (documentResponse && typeof documentResponse === "object") {
          setDocumentData(normalizeDocument(documentResponse));
          setFields(normalizeExtractedFields(documentResponse));
          setAnomalies(normalizeAnomalies(documentResponse));
          setTimeline(normalizeTimeline(documentResponse));

          const fname = documentResponse.filename || documentResponse.fileName || documentResponse.name || "";
          const ftype = getFileType(fname);
          if (ftype === "pdf" || ftype === "image") {
            setPreviewUrl(`${api.defaults.baseURL}/api/documents/${documentId}/download`);
          }
        } else {
          setDocumentData(fallbackDocumentData);
          setFields(fallbackExtractedFields);
          setAnomalies(fallbackDocumentAnomalies);
          setTimeline(fallbackTimeline);
        }
      } catch (err) {
        console.error("Erreur chargement document:", err);
        setError(
          "Impossible de charger le document depuis l'API. Affichage des données de démonstration.",
        );
        setDocumentData(fallbackDocumentData);
        setFields(fallbackExtractedFields);
        setAnomalies(fallbackDocumentAnomalies);
        setTimeline(fallbackTimeline);
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [documentId]);

  const handleDownload = async () => {
    try {
      setActionLoading("download");
      const blob = await downloadDocument(documentId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = documentData.fileName || `document-${documentId}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Erreur téléchargement:", err);
      setError("Impossible de télécharger le document.");
    } finally {
      setActionLoading("");
    }
  };

  const handleValidate = async () => {
    try {
      setActionLoading("validate");
      await updateDocument(documentId, { status: "validated" });
      setDocumentData((prev) => ({ ...prev, status: "Validé" }));
    } catch (err) {
      console.error("Erreur validation:", err);
      setError("Impossible de valider le document.");
    } finally {
      setActionLoading("");
    }
  };

  const handleMarkReview = async () => {
    try {
      setActionLoading("review");
      await updateDocument(documentId, { status: "to_review" });
      setDocumentData((prev) => ({ ...prev, status: "À revoir" }));
    } catch (err) {
      console.error("Erreur marquage:", err);
      setError("Impossible de marquer le document.");
    } finally {
      setActionLoading("");
    }
  };

  const backLink = documentData.caseId
    ? `/crm/${documentData.caseId}`
    : "/crm";

  return (
    <Layout
      title={`Analyse du document #${documentId}`}
      subtitle="Visualise le document, consulte les champs extraits par l'IA, repère les anomalies et prépare la validation métier."
    >
      <div className="space-y-8">
        {error && <ErrorAlert message={error} />}

        {loading ? (
          <SectionCard title="Chargement">
            <div className="py-8 text-center text-slate-500">
              Chargement du document...
            </div>
          </SectionCard>
        ) : (
          <>
            <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <StatCard
                title="Type détecté"
                value={documentData.type}
                subtitle="Classification automatique"
              />
              <StatCard
                title="Confiance globale"
                value={documentData.confidence}
                subtitle="Qualité moyenne d'extraction"
              />
              <StatCard
                title="Anomalies"
                value={String(anomalies.length)}
                subtitle="Points nécessitant vérification"
                badge="Alerte"
                badgeVariant="warning"
              />
              <StatCard
                title="Statut"
                value={documentData.status}
                subtitle="Validation manuelle requise"
                badge="Revue"
                badgeVariant="warning"
              />
            </section>

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Aperçu du document"
                subtitle="Prévisualisation du fichier analysé par le moteur documentaire."
                rightElement={
                  <div className="flex gap-3">
                    <button
                      onClick={handleDownload}
                      disabled={!!actionLoading}
                      className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                      {actionLoading === "download" ? "Téléchargement..." : "Télécharger"}
                    </button>
                    <Link
                      to={backLink}
                      className="rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
                    >
                      Retour dossier
                    </Link>
                  </div>
                }
                className="xl:col-span-2"
              >
                {previewUrl && !previewError ? (
                  getFileType(documentData.fileName) === "pdf" ? (
                    <iframe
                      src={previewUrl}
                      title="Aperçu du document"
                      className="h-[520px] w-full rounded-[28px] border-0"
                      onError={() => setPreviewError(true)}
                    />
                  ) : (
                    <img
                      src={previewUrl}
                      alt="Aperçu du document"
                      className="h-[520px] w-full rounded-[28px] object-contain bg-slate-50"
                      onError={() => setPreviewError(true)}
                    />
                  )
                ) : (
                  <div className="flex h-[520px] items-center justify-center rounded-[28px] border-2 border-dashed border-slate-300 bg-slate-50 text-center">
                    <div>
                      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-lg font-bold text-white">
                        {getFileType(documentData.fileName) === "pdf" ? "PDF" : "DOC"}
                      </div>
                      <p className="mt-4 text-lg font-semibold text-slate-900">
                        Aperçu non disponible
                      </p>
                      <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                        {previewError
                          ? "Impossible de charger l'aperçu. Utilisez le bouton Télécharger."
                          : "Ce format ne supporte pas la prévisualisation en ligne."}
                      </p>
                    </div>
                  </div>
                )}
              </SectionCard>

              <div className="space-y-6">
                <SectionCard title="Résumé rapide">
                  <div className="space-y-4">
                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">Entreprise</p>
                      <p className="mt-1 font-semibold text-slate-900">
                        {documentData.companyName}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">Document</p>
                      <p className="mt-1 font-semibold text-slate-900">
                        {documentData.fileName}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-slate-50 p-4">
                      <p className="text-sm text-slate-500">Dernière analyse</p>
                      <p className="mt-1 font-semibold text-slate-900">
                        {documentData.updatedAt}
                      </p>
                    </div>
                  </div>
                </SectionCard>

                <SectionCard title="Actions">
                  <div className="flex flex-col gap-3">
                    <button
                      onClick={handleValidate}
                      disabled={!!actionLoading}
                      className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
                    >
                      {actionLoading === "validate" ? "Validation..." : "Valider l'extraction"}
                    </button>
                    <button
                      onClick={handleMarkReview}
                      disabled={!!actionLoading}
                      className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-semibold text-white hover:bg-amber-600 disabled:opacity-50"
                    >
                      {actionLoading === "review" ? "En cours..." : "Marquer à revoir"}
                    </button>
                    <button
                      onClick={() => setEditMode((prev) => !prev)}
                      className={`rounded-2xl border px-4 py-3 text-sm font-semibold hover:bg-slate-50 ${editMode ? "border-indigo-300 bg-indigo-50 text-indigo-700" : "border-slate-200 bg-white text-slate-800"}`}
                    >
                      {editMode ? "Terminer l'édition" : "Corriger les champs"}
                    </button>
                  </div>
                </SectionCard>
              </div>
            </section>

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Champs extraits"
                subtitle="Valeurs détectées automatiquement sur le document."
                rightElement={
                  <button
                    onClick={() => {
                      const json = JSON.stringify(fields, null, 2);
                      const blob = new Blob([json], { type: "application/json" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `extracted-fields-${documentId}.json`;
                      a.click();
                      URL.revokeObjectURL(url);
                    }}
                    className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Export JSON
                  </button>
                }
                className="xl:col-span-2"
              >
                <div className="space-y-4">
                  {fields.map((field, index) => (
                    <div
                      key={`${field.label}-${index}`}
                      className="flex flex-col gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 md:flex-row md:items-center md:justify-between"
                    >
                      <div className="flex-1">
                        <p className="text-sm text-slate-500">{field.label}</p>
                        {editMode ? (
                          <input
                            type="text"
                            value={field.value}
                            onChange={(e) => {
                              const updated = [...fields];
                              updated[index] = { ...updated[index], value: e.target.value };
                              setFields(updated);
                            }}
                            className="mt-1 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-base font-semibold text-slate-900 focus:border-indigo-400 focus:outline-none focus:ring-1 focus:ring-indigo-400"
                          />
                        ) : (
                          <p className="mt-1 text-base font-semibold text-slate-900">
                            {field.value}
                          </p>
                        )}
                      </div>

                      <StatusBadge
                        label={`Confiance ${field.confidence || "90%"}`}
                        variant={getConfidenceVariant(field.confidence || "90%")}
                      />
                    </div>
                  ))}
                </div>
              </SectionCard>

              <SectionCard
                title="Pipeline de traitement"
                subtitle="Suivi des étapes d'analyse du document."
              >
                <div className="space-y-4">
                  {timeline.map((item, index) => (
                    <div key={index} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div
                          className={`h-3.5 w-3.5 rounded-full ${
                            item.status === "Terminé" ? "bg-emerald-500" : "bg-amber-500"
                          }`}
                        />
                        {index < timeline.length - 1 && (
                          <div className="mt-2 h-12 w-px bg-slate-200" />
                        )}
                      </div>

                      <div className="pb-3">
                        <p className="font-semibold text-slate-900">{item.step}</p>
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
              subtitle="Points d'attention à vérifier avant validation définitive."
              rightElement={
                <StatusBadge label={`${anomalies.length} alertes`} variant="warning" />
              }
            >
              <div className="grid gap-4 lg:grid-cols-3">
                {anomalies.map((item, index) => (
                  <div
                    key={index}
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
