import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";

export const HomePage = () => {
  return (
    <Layout
      title="Plateforme intelligente de gestion documentaire"
      subtitle="DocuScan AI automatise l'extraction, la vérification et la validation des documents administratifs fournisseurs."
    >
      <section className="grid items-stretch gap-6 lg:grid-cols-3">
        <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm lg:col-span-2">
          <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-slate-100 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-40 w-40 rounded-full bg-emerald-100 blur-3xl" />

          <div className="relative">
            <span className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
              Hackathon 2026 — OCR + NLP + Détection d'anomalies
            </span>

            <h2 className="mt-5 max-w-2xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl">
              Déposez vos documents, l'IA s'occupe du reste
            </h2>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
              Factures, attestations URSSAF, Kbis, RIB — déposez-les et le pipeline
              les classifie, extrait les données clés, détecte les incohérences et
              pré-remplit automatiquement vos dossiers fournisseurs et contrôles de conformité.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/upload"
                className="inline-flex items-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                Déposer des documents
              </Link>
              <Link
                to="/crm"
                className="inline-flex items-center rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-50"
              >
                Voir les dossiers
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Comment ça marche
          </p>

          <div className="mt-6 space-y-4">
            <Link to="/upload" className="block rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white font-bold">
                1
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Dépôt</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Importez vos documents (PDF, images, DOCX). Le pipeline Airflow se déclenche automatiquement.
              </p>
            </Link>

            <Link to="/dashboard" className="block rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white font-bold">
                2
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Documents</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Suivez le traitement : OCR, extraction d'entités, classification, détection d'anomalies.
              </p>
            </Link>

            <Link to="/crm" className="block rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:border-slate-300 hover:bg-white">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white font-bold">
                3
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Dossiers & Conformité</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Consultez les fiches fournisseurs auto-remplies et validez la conformité des documents.
              </p>
            </Link>
          </div>
        </div>
      </section>
    </Layout>
  );
};
