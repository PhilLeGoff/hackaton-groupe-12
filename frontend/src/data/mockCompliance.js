export const globalChecks = [
  { label: "KBIS présent", passed: true },
  { label: "RIB présent", passed: true },
  { label: "Attestation URSSAF présente", passed: false },
  { label: "SIRET cohérent sur les pièces", passed: true },
  { label: "Adresse cohérente", passed: true },
  { label: "Document principal lisible", passed: false },
];

export const requiredDocuments = [
  { name: "KBIS", status: "Présent", type: "success" },
  { name: "RIB", status: "Présent", type: "success" },
  { name: "Attestation URSSAF", status: "Manquant", type: "danger" },
  { name: "Facture fournisseur", status: "Présent", type: "success" },
];

export const complianceAnomalies = [
  {
    title: "Attestation URSSAF manquante",
    description:
      "Le dossier ne contient pas d’attestation de vigilance URSSAF exploitable pour la vérification réglementaire.",
    level: "danger",
  },
  {
    title: "Lisibilité partielle d’un document",
    description:
      "Le document principal présente des zones floues qui peuvent réduire la fiabilité de certains contrôles automatiques.",
    level: "warning",
  },
  {
    title: "Revue humaine recommandée",
    description:
      "Le moteur suggère une validation manuelle avant toute décision finale sur le dossier.",
    level: "info",
  },
];

export const decisionHistory = [
  {
    action: "Dossier créé",
    date: "16/03/2026 • 13:55",
    status: "Terminé",
  },
  {
    action: "Analyse automatique exécutée",
    date: "16/03/2026 • 14:00",
    status: "Terminé",
  },
  {
    action: "Contrôle conformité lancé",
    date: "16/03/2026 • 14:02",
    status: "Terminé",
  },
  {
    action: "Décision finale",
    date: "En attente",
    status: "À faire",
  },
];