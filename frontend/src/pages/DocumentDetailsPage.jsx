import { useParams, Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import {
  extractedFields as fallbackExtractedFields,
  documentAnomalies as fallbackDocumentAnomalies,
  timeline as fallbackTimeline,
} from "../data/mockDocuments";
import { getDocumentById, getDocumentExtraction } from "../api/documents";

const normalizeDocument = (item) => ({
  id: item.id || item._id || "N/A",
  type: item.type || item.documentType || item.document_type || "Document",
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  fileName: item.fileName || item.filename || item.name || "document.pdf",
  confidence: item.confidence || item.confidenceScore || "94%",
  status: item.status || item.analysisStatus || "À revoir",
  updatedAt: item.updatedAt || item.updated_at || "Aujourd’hui",
});

const normalizeExtraction = (data) => {
  if (Array.isArray(data)) return data;

  if (data?.fields && Array.isArray(data.fields)) {
    return data.fields;
  }

  if (data && typeof data === "object") {
    return Object.entries(data).map(([key, value]) => ({
      label: key,
      value: String(value),
      confidence: "90%",
    }));
  }

  return fallbackExtractedFields;
};

const getConfidenceVariant = (confidence) => {
  const value = parseInt(confidence, 10);

  if (value >= 95) return "success";
  if (value >= 85) return "warning";
  return "danger";
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

  const [documentData, setDocumentData] = useState({
    type: "Facture",
    companyName: "Société Alpha",
    fileName: "facture_alpha.pdf",
    confidence: "94%",
    status: "À revoir",
    updatedAt: "Aujourd’hui à 14:00",
  });

  const [fields, setFields] = useState(fallbackExtractedFields);
  const [anomalies] = useState(fallbackDocumentAnomalies);
  const [timeline] = useState(fallbackTimeline);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const loadDocument = async () => {
      try {
        setLoading(true);
        setError("");

        const [documentResponse, extractionResponse] = await Promise.all([
          getDocumentById(documentId),
          getDocumentExtraction(documentId),
        ]);

        if (documentResponse && typeof documentResponse === "object") {
          setDocumentData(normalizeDocument(documentResponse));
        }

        if (extractionResponse) {
          setFields(normalizeExtraction(extractionResponse));
        } else {
          setFields(fallbackExtractedFields);
        }
      } catch (err) {
        console.error("Erreur chargement document:", err);
        setError("API indisponible, affichage des données de démonstration.");
        setDocumentData({
          type: "Facture",
          companyName: "Société Alpha",
          fileName: "facture_alpha.pdf",
          confidence: "94%",
          status: "À revoir",
          updatedAt: "Aujourd’hui à 14:00",
        });
        setFields(fallbackExtractedFields);
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [documentId]);

  return (
    <Layout
      title={`Analyse du document #${documentId}`}
      subtitle="Visualise le document, consulte les champs extraits par l’IA, repère les anomalies et prépare la validation métier."
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
                subtitle="Qualité moyenne d’extraction"
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
                    <button className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                      Télécharger
                    </button>
                    <Link
                      to="/crm/1"
                      className="rounded-2xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-800"
                    >
                      Retour dossier
                    </Link>
                  </div>
                }
                className="xl:col-span-2"
              >
                <div className="flex h-[520px] items-center justify-center rounded-[28px] border-2 border-dashed border-slate-300 bg-slate-50 text-center">
                  <div>
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-slate-900 text-lg font-bold text-white">
                      PDF
                    </div>
                    <p className="mt-4 text-lg font-semibold text-slate-900">
                      Aperçu du document
                    </p>
                    <p className="mt-2 max-w-sm text-sm leading-6 text-slate-500">
                      Cette zone affichera l’aperçu PDF ou image une fois le viewer connecté à l’API.
                    </p>
                  </div>
                </div>
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
                    <button className="rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700">
                      Valider l’extraction
                    </button>
                    <button className="rounded-2xl bg-amber-500 px-4 py-3 text-sm font-semibold text-white hover:bg-amber-600">
                      Marquer à revoir
                    </button>
                    <button className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 hover:bg-slate-50">
                      Corriger les champs
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
                  <button className="rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50">
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
                      <div>
                        <p className="text-sm text-slate-500">{field.label}</p>
                        <p className="mt-1 text-base font-semibold text-slate-900">
                          {field.value}
                        </p>
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
                subtitle="Suivi des étapes d’analyse du document."
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
              subtitle="Points d’attention à vérifier avant validation définitive."
              rightElement={<StatusBadge label={`${anomalies.length} alertes`} variant="warning" />}
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