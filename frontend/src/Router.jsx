import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { CRMPage } from "./pages/CRMPage";
import { CaseDetailsPage } from "./pages/CaseDetailsPage";
import { DocumentDetailsPage } from "./pages/DocumentDetailsPage";
import { CompliancePage } from "./pages/CompliancePage";
import { UploadPage } from "./pages/UploadPage";
import { DashboardPage } from "./pages/DashboardPage";

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
      </Routes>
    </BrowserRouter>
  );
};