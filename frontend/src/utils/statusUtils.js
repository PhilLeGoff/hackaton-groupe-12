/** Normalize backend status strings to consistent French labels. */
export const normalizeStatus = (status) => {
  if (!status) return "Inconnu";
  switch (status.toLowerCase().replace(/[_ ]/g, "")) {
    case "completed":
    case "analyseterminee":
    case "analyseterminée":
      return "Analysé";
    case "validated":
    case "conforme":
    case "compliant":
      return "Validé";
    case "toreview":
    case "averifier":
    case "àvérifier":
    case "averifier":
      return "À vérifier";
    case "processing":
    case "encours":
      return "En cours";
    case "uploaded":
    case "enattente":
      return "En attente";
    case "error":
    case "erreur":
      return "Erreur";
    case "nonconforme":
    case "noncompliant":
    case "rejected":
    case "rejeté":
    case "rejete":
      return "Non conforme";
    case "pending":
      return "En attente";
    default:
      return status;
  }
};

/** Return variant for StatusBadge based on normalized status. */
export const getStatusVariant = (status) => {
  const n = normalizeStatus(status);
  switch (n) {
    case "Validé":
    case "Analysé":
      return "success";
    case "À vérifier":
    case "En cours":
    case "En attente":
      return "warning";
    case "Erreur":
    case "Non conforme":
      return "danger";
    default:
      return "default";
  }
};

/** Badge style classes for DashboardPage. */
export const getStatusBadgeClass = (status) => {
  const n = normalizeStatus(status);
  switch (n) {
    case "Validé":
    case "Analysé":
      return "bg-emerald-50 text-emerald-700 border-emerald-200";
    case "À vérifier":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "En cours":
    case "En attente":
      return "bg-blue-50 text-blue-700 border-blue-200";
    case "Erreur":
    case "Non conforme":
      return "bg-red-50 text-red-700 border-red-200";
    default:
      return "bg-slate-50 text-slate-600 border-slate-200";
  }
};

/** Check if a document is "done" (processed, not pending/processing). */
export const isDone = (status) => {
  const n = normalizeStatus(status);
  return ["Analysé", "Validé", "À vérifier", "Erreur", "Non conforme"].includes(n);
};
