import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { CRMPage } from "./pages/CRMPage";
import { CaseDetailsPage } from "./pages/CaseDetailsPage";
import { DocumentDetailsPage } from "./pages/DocumentDetailsPage";
import { CompliancePage } from "./pages/CompliancePage";
import { UploadPage } from "./pages/UploadPage";
import { DashboardPage } from "./pages/DashboardPage";
import { Layout } from "./components/Layout";

const NotFoundPage = () => (
  <Layout title="Page introuvable" subtitle="La page que vous cherchez n'existe pas.">
    <div className="flex flex-col items-center justify-center py-16">
      <p className="text-6xl font-bold text-slate-300">404</p>
      <p className="mt-4 text-lg text-slate-500">Cette page n'existe pas ou a été déplacée.</p>
      <Link
        to="/"
        className="mt-6 rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800"
      >
        Retour à l'accueil
      </Link>
    </div>
  </Layout>
);

export const Router = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/crm" element={<CRMPage />} />
        <Route path="/crm/:caseId" element={<CaseDetailsPage />} />
        <Route path="/documents/:documentId" element={<DocumentDetailsPage />} />
        <Route path="/compliance/:caseId" element={<CompliancePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </BrowserRouter>
  );
};
