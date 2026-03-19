import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ErrorAlert } from "../components/ErrorAlert";
const fallbackCaseSummary = {
  companyName: "—",
  siret: "—",
  status: "En attente",
  documents: 0,
  contact: "—",
  sector: "—",
  updatedAt: "—",
};
import { getCaseById, getAutofill, getDocumentsByCase } from "../api/cases";
import { downloadDocument } from "../api/documents";
import { api } from "../api/axios";
import { normalizeStatus, getStatusVariant } from "../utils/statusUtils";

const getFileIcon = (filename) => {
  if (!filename) return "DOC";
  const ext = filename.split(".").pop().toLowerCase();
  if (ext === "pdf") return "PDF";
  if (["jpg", "jpeg", "png"].includes(ext)) return "IMG";
  if (ext === "docx") return "DOC";
  return "TXT";
};

const normalizeCase = (item) => ({
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  siret: item.siret || item.companySiret || "Non renseigné",
  status: normalizeStatus(item.status),
  documents: typeof item.documents === "number" ? item.documents : (Array.isArray(item.documents) ? item.documents.length : (item.documentsCount ?? 0)),
  contact: item.contact || item.email || "Non renseigné",
  sector: item.sector || item.activity || "Non renseigné",
  updatedAt: item.updatedAt || item.updated_at || "Récemment",
});

const emptyForm = {
  company_name: "",
  siret: "",
  vat: "",
  iban: "",
  address: "",
  contact: "",
  sector: "",
  urssaf_status: "",
  urssaf_expiry: "",
};

export const CaseDetailsPage = () => {
  const { caseId } = useParams();
  const [caseData, setCaseData] = useState(fallbackCaseSummary);
  const [documents, setDocuments] = useState([]);
  const [autofill, setAutofill] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [downloadingId, setDownloadingId] = useState(null);

  // Formulaire auto-rempli
  const [form, setForm] = useState(emptyForm);
  const [filledFields, setFilledFields] = useState({});
  const [autoFilling, setAutoFilling] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const loadAll = async () => {
      try {
        setLoading(true);
        setError("");

        const [caseResult, docsResult, autofillResult] = await Promise.allSettled([
          getCaseById(caseId),
          getDocumentsByCase(caseId),
          getAutofill(caseId),
        ]);

        if (caseResult.status === "fulfilled" && caseResult.value) {
          const c = normalizeCase(caseResult.value);
          setCaseData(c);
          setForm((prev) => ({
            ...prev,
            company_name: c.companyName !== "Entreprise inconnue" ? c.companyName : "",
            siret: c.siret !== "Non renseigné" ? c.siret : "",
            contact: c.contact !== "Non renseigné" ? c.contact : "",
            sector: c.sector !== "Non renseigné" ? c.sector : "",
          }));
        } else {
          setCaseData(fallbackCaseSummary);
        }

        if (docsResult.status === "fulfilled" && docsResult.value) {
          const items = docsResult.value.data || docsResult.value;
          if (Array.isArray(items)) {
            setDocuments(items);
          }
        }

        if (autofillResult.status === "fulfilled" && autofillResult.value) {
          const af = autofillResult.value;
          setAutofill(af);

          // Auto-remplissage automatique au chargement
          const autoFields = [
            ["company_name", af.company_name],
            ["siret", af.siret],
            ["vat", af.vat],
            ["iban", af.compliance?.iban],
            ["address", af.address],
            ["urssaf_status", af.compliance?.urssaf_valid ? "Valide" : "Non valide"],
            ["urssaf_expiry", af.compliance?.urssaf_expiry],
          ];
          const newForm = { ...emptyForm };
          const newFilled = {};
          for (const [key, value] of autoFields) {
            if (value) {
              newForm[key] = value;
              newFilled[key] = true;
            }
          }
          // Garder contact/sector du case s'ils existent
          if (caseResult.status === "fulfilled" && caseResult.value) {
            const cv = caseResult.value;
            if (cv.contact) newForm.contact = cv.contact;
            if (cv.sector) newForm.sector = cv.sector;
          }
          setForm(newForm);
          setFilledFields(newFilled);
        }

        if (caseResult.status === "rejected") {
          setError("API indisponible, affichage des données de démonstration.");
        }
      } catch (err) {
        console.error("Erreur chargement dossier:", err);
        setError("API indisponible, affichage des données de démonstration.");
        setCaseData(fallbackCaseSummary);
      } finally {
        setLoading(false);
      }
    };

    loadAll();
  }, [caseId]);

  const handleAutoFill = async () => {
    if (!autofill) return;
    setAutoFilling(true);
    const filled = {};
    const newForm = { ...form };

    // Simulate progressive fill with small delays for visual effect
    const fields = [
      ["company_name", autofill.company_name],
      ["siret", autofill.siret],
      ["vat", autofill.vat],
      ["iban", autofill.compliance?.iban],
      ["address", autofill.address],
      ["urssaf_status", autofill.compliance?.urssaf_valid ? "Valide" : "Non valide"],
      ["urssaf_expiry", autofill.compliance?.urssaf_expiry],
    ];

    for (const [key, value] of fields) {
      if (value) {
        newForm[key] = value;
        filled[key] = true;
      }
    }

    // Progressive animation — fill one field at a time
    for (let i = 0; i < fields.length; i++) {
      const [key, value] = fields[i];
      if (value) {
        await new Promise((r) => setTimeout(r, 150));
        setForm((prev) => ({ ...prev, [key]: value }));
        setFilledFields((prev) => ({ ...prev, [key]: true }));
      }
    }

    setAutoFilling(false);
  };

  const handleFormChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSaveForm = async () => {
    try {
      setSaving(true);
      const payload = {};
      // Only send non-empty fields
      if (form.company_name) payload.company_name = form.company_name;
      if (form.siret) payload.siret = form.siret;
      if (form.contact) payload.contact = form.contact;
      if (form.sector) payload.sector = form.sector;
      if (form.vat) payload.vat = form.vat;
      if (form.iban) payload.iban = form.iban;
      if (form.address) payload.address = form.address;
      await api.put(`/api/cases/${caseId}`, payload);
      setError("");
    } catch (err) {
      console.error("Erreur sauvegarde:", err);
      setError("Impossible de sauvegarder les modifications.");
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async (docId, filename) => {
    try {
      setDownloadingId(docId);
      const blob = await downloadDocument(docId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || `document-${docId}`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Erreur téléchargement:", err);
    } finally {
      setDownloadingId(null);
    }
  };

  const fieldClass = (key) =>
    `w-full rounded-xl border px-4 py-3 text-sm outline-none transition-all duration-500 ${
      filledFields[key]
        ? "border-emerald-400 bg-emerald-50 ring-2 ring-emerald-200 text-slate-900 font-semibold"
        : "border-slate-200 bg-slate-50 text-slate-800 focus:border-slate-400 focus:bg-white"
    }`;

  const formFields = [
    { key: "company_name", label: "Raison sociale", placeholder: "Nom de l'entreprise" },
    { key: "siret", label: "SIRET", placeholder: "14 chiffres" },
    { key: "vat", label: "N° TVA intracommunautaire", placeholder: "FR + 11 chiffres" },
    { key: "iban", label: "IBAN", placeholder: "FR76..." },
    { key: "address", label: "Adresse", placeholder: "Adresse du siège" },
    { key: "contact", label: "Contact", placeholder: "Email ou téléphone" },
    { key: "sector", label: "Secteur d'activité", placeholder: "Services, Industrie..." },
    { key: "urssaf_status", label: "Statut URSSAF", placeholder: "Valide / Non valide" },
    { key: "urssaf_expiry", label: "Expiration URSSAF", placeholder: "YYYY-MM-DD" },
  ];

  return (
    <Layout
      title={`Dossier fournisseur`}
      subtitle="Fiche auto-remplie par l'IA à partir des documents analysés (factures, KBIS, URSSAF, RIB)."
    >
      <div className="space-y-8">
        {error && <ErrorAlert message={error} />}

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
                value={documents.length || caseData.documents}
                subtitle="Pièces associées au dossier"
              />
            </section>

            {/* Formulaire fournisseur auto-rempli par l'IA */}
            <SectionCard
              title="Informations fournisseur"
              subtitle="Champs extraits automatiquement par l'IA depuis les documents du dossier. Cliquez sur « Auto-remplir » pour lancer l'extraction."
              rightElement={
                <div className="flex gap-3">
                  <button
                    onClick={handleAutoFill}
                    disabled={autoFilling || !autofill}
                    className="rounded-2xl bg-emerald-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {autoFilling ? "Remplissage en cours..." : "Auto-remplir depuis l'IA"}
                  </button>
                  <button
                    onClick={handleSaveForm}
                    disabled={saving}
                    className="rounded-2xl bg-slate-900 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-800 disabled:opacity-50"
                  >
                    {saving ? "Sauvegarde..." : "Enregistrer"}
                  </button>
                </div>
              }
            >
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {formFields.map(({ key, label, placeholder }) => (
                  <div key={key}>
                    <label className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700">
                      {label}
                      {filledFields[key] && (
                        <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-700">
                          IA
                        </span>
                      )}
                    </label>
                    <input
                      type="text"
                      value={form[key]}
                      onChange={(e) => handleFormChange(key, e.target.value)}
                      placeholder={placeholder}
                      className={fieldClass(key)}
                    />
                  </div>
                ))}
              </div>

              {Object.keys(filledFields).length > 0 && (
                <p className="mt-4 text-xs text-emerald-600">
                  {Object.keys(filledFields).length} champ(s) rempli(s) automatiquement par l'IA depuis les documents analysés.
                </p>
              )}
            </SectionCard>

            {/* Vérification inter-documents */}
            {autofill?.compliance && (
              <SectionCard
                title="Vérification inter-documents"
                subtitle="Cohérence des informations entre les différentes pièces du dossier."
              >
                <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                  <div className={`rounded-2xl border p-4 ${autofill.compliance.all_sirets_match ? "bg-emerald-50 border-emerald-200" : "bg-rose-50 border-rose-200"}`}>
                    <p className="text-sm text-slate-500">Cohérence SIRET</p>
                    <p className={`mt-1 font-semibold ${autofill.compliance.all_sirets_match ? "text-emerald-700" : "text-rose-700"}`}>
                      {autofill.compliance.all_sirets_match ? "Tous les SIRET correspondent" : "SIRET incohérent entre documents"}
                    </p>
                  </div>
                  <div className={`rounded-2xl border p-4 ${autofill.compliance.urssaf_valid ? "bg-emerald-50 border-emerald-200" : "bg-rose-50 border-rose-200"}`}>
                    <p className="text-sm text-slate-500">Attestation URSSAF</p>
                    <p className={`mt-1 font-semibold ${autofill.compliance.urssaf_valid ? "text-emerald-700" : "text-rose-700"}`}>
                      {autofill.compliance.urssaf_valid ? "Valide" : "Expirée ou absente"}
                      {autofill.compliance.urssaf_expiry && ` — exp. ${autofill.compliance.urssaf_expiry}`}
                    </p>
                  </div>
                  <div className={`rounded-2xl border p-4 ${autofill.compliance.kbis_present ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`}>
                    <p className="text-sm text-slate-500">Extrait KBIS</p>
                    <p className={`mt-1 font-semibold ${autofill.compliance.kbis_present ? "text-emerald-700" : "text-amber-700"}`}>
                      {autofill.compliance.kbis_present ? "Présent" : "Manquant"}
                    </p>
                  </div>
                  <div className={`rounded-2xl border p-4 ${autofill.compliance.rib_present ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`}>
                    <p className="text-sm text-slate-500">RIB</p>
                    <p className={`mt-1 font-semibold ${autofill.compliance.rib_present ? "text-emerald-700" : "text-amber-700"}`}>
                      {autofill.compliance.rib_present ? "Présent" : "Manquant"}
                    </p>
                  </div>
                </div>

                {autofill.compliance.anomalies?.length > 0 && (
                  <div className="mt-4 space-y-3">
                    <p className="text-sm font-semibold text-rose-700">Anomalies inter-documents détectées :</p>
                    {autofill.compliance.anomalies.map((a, i) => (
                      <div key={i} className="rounded-2xl border border-rose-200 bg-rose-50 p-4">
                        <p className="font-medium text-rose-800">{a.field || "Anomalie"}</p>
                        <p className="mt-1 text-sm text-rose-700">{a.message}</p>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            )}

            <section className="grid gap-6 xl:grid-cols-3">
              <SectionCard
                title="Actions"
                className="xl:col-span-1"
              >
                <div className="grid gap-3">
                  <Link
                    to={`/compliance/${caseId}`}
                    className="inline-flex items-center justify-center rounded-2xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
                  >
                    Voir conformité
                  </Link>

                  <Link
                    to="/upload"
                    className="inline-flex items-center justify-center rounded-2xl bg-slate-900 px-4 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                  >
                    Ajouter un document
                  </Link>

                  <Link
                    to="/crm"
                    className="inline-flex items-center justify-center rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"
                  >
                    Retour aux dossiers
                  </Link>
                </div>
              </SectionCard>

              <SectionCard
                title="Documents du dossier"
                subtitle="Pièces analysées par le pipeline IA."
                className="xl:col-span-2"
              >
                {documents.length === 0 ? (
                  <div className="py-10 text-center text-slate-500">
                    <p className="text-lg font-semibold text-slate-900">Aucun document</p>
                    <p className="mt-2 text-sm">Les documents apparaîtront ici après upload et traitement par le pipeline IA.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {documents.map((doc) => (
                      <div
                        key={doc.id}
                        className="group rounded-3xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white"
                      >
                        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                          <div className="flex items-start gap-4">
                            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white">
                              {getFileIcon(doc.name)}
                            </div>
                            <div>
                              <p className="text-base font-semibold text-slate-900">
                                {doc.name || "Document sans nom"}
                              </p>
                              <div className="mt-2 flex flex-wrap items-center gap-2">
                                {doc.type && (
                                  <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-medium text-slate-700">
                                    {doc.type}
                                  </span>
                                )}
                                <StatusBadge
                                  label={doc.status || "En cours"}
                                  variant={getStatusVariant(doc.status)}
                                />
                                {doc.confidence > 0 && (
                                  <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600">
                                    Confiance : {typeof doc.confidence === "number" ? `${doc.confidence}%` : doc.confidence}
                                  </span>
                                )}
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
                            <button
                              onClick={() => handleDownload(doc.id, doc.name)}
                              disabled={downloadingId === doc.id}
                              className="inline-flex items-center rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50"
                            >
                              {downloadingId === doc.id ? "..." : "Télécharger"}
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            </section>
          </>
        )}
      </div>
    </Layout>
  );
};
