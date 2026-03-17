export const mockDocuments = [
  {
    id: "101",
    name: "facture_alpha.pdf",
    type: "Facture",
    status: "Analyse terminée",
    confidence: "96%",
  },
  {
    id: "102",
    name: "kbis_alpha.pdf",
    type: "KBIS",
    status: "Analyse terminée",
    confidence: "93%",
  },
  {
    id: "103",
    name: "rib_alpha.pdf",
    type: "RIB",
    status: "À vérifier",
    confidence: "81%",
  },
];

export const extractedFields = [
  { label: "Type détecté", value: "Facture", confidence: "98%" },
  { label: "Entreprise", value: "Société Alpha", confidence: "96%" },
  { label: "SIRET", value: "12345678900011", confidence: "94%" },
  { label: "Montant TTC", value: "1 250 €", confidence: "92%" },
  { label: "Date document", value: "16/03/2026", confidence: "95%" },
  { label: "Référence facture", value: "FAC-2026-014", confidence: "89%" },
];

export const documentAnomalies = [
  {
    title: "TVA partiellement détectée",
    description:
      "Le montant TTC est bien identifié, mais la structure de TVA manque de clarté sur le scan analysé.",
    level: "warning",
  },
  {
    title: "Qualité de scan moyenne",
    description:
      "Certaines zones du document sont légèrement floues, ce qui peut réduire la fiabilité de l’extraction.",
    level: "warning",
  },
  {
    title: "Vérification humaine recommandée",
    description:
      "Une revue manuelle est conseillée avant validation définitive du document.",
    level: "info",
  },
];

export const timeline = [
  { step: "Upload du document", status: "Terminé", date: "16/03/2026 • 13:58" },
  { step: "Classification automatique", status: "Terminé", date: "16/03/2026 • 13:59" },
  { step: "Extraction des champs", status: "Terminé", date: "16/03/2026 • 14:00" },
  { step: "Contrôle conformité", status: "En attente", date: "16/03/2026 • 14:01" },
];