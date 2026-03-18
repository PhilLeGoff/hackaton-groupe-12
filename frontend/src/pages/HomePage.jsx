import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";

export const HomePage = () => {
  return (
    <Layout
      title="Plateforme intelligente de gestion documentaire"
      subtitle="DocuScan AI centralise les dossiers, analyse les documents extraits par l’IA et facilite le contrôle de conformité."
    >
      <section className="grid items-stretch gap-6 lg:grid-cols-3">
        <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-white p-8 shadow-sm lg:col-span-2">
          <div className="absolute right-0 top-0 h-40 w-40 rounded-full bg-slate-100 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-40 w-40 rounded-full bg-emerald-100 blur-3xl" />

          <div className="relative">
            <span className="inline-flex rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-600">
              Hackathon • Front React CRM & Conformité
            </span>

            <h2 className="mt-5 max-w-2xl text-4xl font-bold leading-tight text-slate-900 md:text-5xl">
              DocuScan AI pour centraliser, vérifier et valider les documents
            </h2>

            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
              Cette interface permet de suivre les dossiers, consulter les documents analysés,
              afficher les champs extraits automatiquement et prendre une décision de conformité.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                to="/crm"
                className="inline-flex items-center rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800"
              >
                Ouvrir le CRM
              </Link>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wide text-slate-500">
            Modules disponibles
          </p>

          <div className="mt-6 space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-white">
                1
              </div>
              <h3 className="text-lg font-semibold text-slate-900">CRM documentaire</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Liste des dossiers, informations d’entreprise, statut et accès rapide aux documents.
              </p>
              <Link
                to="/crm"
                className="mt-4 inline-flex text-sm font-semibold text-slate-900 hover:text-slate-700"
              >
                Accéder au module →
              </Link>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-600 text-white">
                2
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Upload de documents</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Déposez vos fichiers (PDF, images, DOCX) pour lancer l’extraction IA automatique.
              </p>
              <Link
                to="/upload"
                className="mt-4 inline-flex text-sm font-semibold text-slate-900 hover:text-slate-700"
              >
                Uploader un document →
              </Link>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
              <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white">
                3
              </div>
              <h3 className="text-lg font-semibold text-slate-900">Dashboard pipeline</h3>
              <p className="mt-2 text-sm leading-6 text-slate-600">
                Suivi en temps réel du traitement des documents : OCR, NER, classification, validation.
              </p>
              <Link
                to="/dashboard"
                className="mt-4 inline-flex text-sm font-semibold text-slate-900 hover:text-slate-700"
              >
                Voir le dashboard →
              </Link>
            </div>
          </div>
        </div>
      </section>
    </Layout>
  );
};