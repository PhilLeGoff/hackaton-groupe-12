import { useEffect, useMemo, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { Layout } from "../components/Layout";
import { StatCard } from "../components/StatCard";
import { SectionCard } from "../components/SectionCard";
import { StatusBadge } from "../components/StatusBadge";
import { ErrorAlert } from "../components/ErrorAlert";
import { getCases, createCase } from "../api/cases";
import { normalizeStatus, getStatusVariant } from "../utils/statusUtils";

const normalizeCase = (item) => ({
  id: item.id || item._id || "N/A",
  companyName:
    item.companyName || item.company_name || item.name || "Entreprise inconnue",
  siret: item.siret || item.companySiret || "Non renseigné",
  status: normalizeStatus(item.status),
  documents: typeof item.documents === "number" ? item.documents : (Array.isArray(item.documents) ? item.documents.length : (item.documentsCount ?? 0)),
  owner: item.owner || item.department || "Non assigné",
  updatedAt: item.updatedAt || item.updated_at || "Récemment",
});

export const CRMPage = () => {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("Tous");
  const [showNewCase, setShowNewCase] = useState(false);
  const [newCase, setNewCase] = useState({ company_name: "", siret: "", contact: "", sector: "" });
  const [creating, setCreating] = useState(false);

  const fetchCases = useCallback(async () => {
    try {
      setLoading(true);
      setError("");

      const data = await getCases();
      const items = data?.data || data;

      if (Array.isArray(items)) {
        setCases(items.map(normalizeCase));
      } else {
        setCases([]);
      }
    } catch (err) {
      console.error("Erreur chargement dossiers:", err);
      setError(
        "Impossible de charger les dossiers depuis l'API.",
      );
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCases();
  }, [fetchCases]);

  const handleCreateCase = async (e) => {
    e.preventDefault();
    if (!newCase.company_name || !newCase.siret) return;
    try {
      setCreating(true);
      await createCase(newCase);
      setShowNewCase(false);
      setNewCase({ company_name: "", siret: "", contact: "", sector: "" });
      fetchCases();
    } catch (err) {
      console.error("Erreur création dossier:", err);
      setError("Impossible de créer le dossier.");
    } finally {
      setCreating(false);
    }
  };

  const handleExport = () => {
    const json = JSON.stringify(cases, null, 2);
    const blob = new Blob([json], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `crm-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const filteredCases = useMemo(() => {
    let result = [...cases];

    if (activeFilter === "À vérifier") {
      result = result.filter((item) => item.status === "À vérifier" || item.status === "En attente");
    } else if (activeFilter === "Conforme") {
      result = result.filter((item) => item.status === "Conforme" || item.status === "Validé");
    } else if (activeFilter === "Non conforme") {
      result = result.filter((item) => item.status === "Non conforme" || item.status === "Erreur");
    }

    const value = search.trim().toLowerCase();

    if (!value) return result;

    return result.filter((item) => {
      return (
        item.companyName.toLowerCase().includes(value) ||
        item.siret.toLowerCase().includes(value) ||
        item.status.toLowerCase().includes(value) ||
        item.owner.toLowerCase().includes(value)
      );
    });
  }, [cases, search, activeFilter]);

  const totalCases = cases.length;
  const compliantCases = cases.filter((item) => item.status === "Conforme" || item.status === "Validé").length;
  const reviewCases = cases.filter((item) => item.status === "À vérifier" || item.status === "En attente").length;
  const nonCompliantCases = cases.filter((item) => item.status === "Non conforme" || item.status === "Erreur").length;

  const filterBtnClass = (label) =>
    activeFilter === label
      ? "rounded-full bg-slate-900 px-4 py-2 text-sm font-medium text-white"
      : "rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50";

  return (
    <Layout
      title="Dossiers fournisseurs"
      subtitle="Liste des dossiers d'entreprise créés automatiquement par l'IA. Chaque dossier regroupe les documents d'un même fournisseur (par SIRET)."
    >
      <div className="space-y-8">
        <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <StatCard
            title="Dossiers totaux"
            value={totalCases}
            subtitle="Vue consolidée de tous les dossiers documentaires."
            badge="Global"
          />

          <StatCard
            title="Conformes"
            value={compliantCases}
            subtitle="Dossiers validés et prêts pour traitement final."
            badge="OK"
            badgeVariant="success"
          />

          <StatCard
            title="À vérifier"
            value={reviewCases}
            subtitle="Dossiers nécessitant une validation humaine."
            badge="Revue"
            badgeVariant="warning"
          />

          <StatCard
            title="Non conformes"
            value={nonCompliantCases}
            subtitle="Dossiers comportant des anomalies ou pièces manquantes."
            badge="Alerte"
            badgeVariant="danger"
          />
        </section>

        {error && <ErrorAlert message={error} />}

        {/* Modal nouveau dossier */}
        {showNewCase && (
          <SectionCard title="Nouveau dossier" subtitle="Créer un dossier fournisseur manuellement.">
            <form onSubmit={handleCreateCase} className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Raison sociale *</label>
                <input
                  type="text"
                  value={newCase.company_name}
                  onChange={(e) => setNewCase((p) => ({ ...p, company_name: e.target.value }))}
                  placeholder="Société Alpha"
                  required
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 focus:bg-white"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">SIRET *</label>
                <input
                  type="text"
                  value={newCase.siret}
                  onChange={(e) => setNewCase((p) => ({ ...p, siret: e.target.value }))}
                  placeholder="12345678900011"
                  required
                  maxLength={14}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 focus:bg-white"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Contact</label>
                <input
                  type="text"
                  value={newCase.contact}
                  onChange={(e) => setNewCase((p) => ({ ...p, contact: e.target.value }))}
                  placeholder="email@entreprise.fr"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 focus:bg-white"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Secteur</label>
                <input
                  type="text"
                  value={newCase.sector}
                  onChange={(e) => setNewCase((p) => ({ ...p, sector: e.target.value }))}
                  placeholder="Services, Industrie..."
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none focus:border-slate-400 focus:bg-white"
                />
              </div>
              <div className="flex gap-3 md:col-span-2">
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-2xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                >
                  {creating ? "Création..." : "Créer le dossier"}
                </button>
                <button
                  type="button"
                  onClick={() => setShowNewCase(false)}
                  className="rounded-2xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                  Annuler
                </button>
              </div>
            </form>
          </SectionCard>
        )}

        <SectionCard>
          <div className="space-y-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="w-full sm:max-w-md">
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Rechercher une entreprise, un SIRET..."
                  className="w-full rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:bg-white"
                />
              </div>
              <button
                onClick={() => setShowNewCase(true)}
                className="w-full shrink-0 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 sm:w-auto"
              >
                + Nouveau dossier
              </button>
            </div>

            <div className="flex flex-wrap gap-2">
              <button className={filterBtnClass("Tous")} onClick={() => setActiveFilter("Tous")}>Tous</button>
              <button className={filterBtnClass("Conforme")} onClick={() => setActiveFilter("Conforme")}>Conforme</button>
              <button className={filterBtnClass("À vérifier")} onClick={() => setActiveFilter("À vérifier")}>À vérifier</button>
              <button className={filterBtnClass("Non conforme")} onClick={() => setActiveFilter("Non conforme")}>Non conforme</button>
            </div>
          </div>
        </SectionCard>

        <SectionCard
          title="Liste des dossiers"
          subtitle={`Filtre actif : ${activeFilter}`}
          rightElement={
            <div className="flex items-center gap-2">
              <button
                onClick={handleExport}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
              >
                Exporter
              </button>
              <button
                className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                onClick={fetchCases}
                disabled={loading}
              >
                {loading ? "..." : "Actualiser"}
              </button>
            </div>
          }
          className="overflow-hidden p-0"
        >
          {loading ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Chargement des dossiers...
            </div>
          ) : filteredCases.length === 0 ? (
            <div className="px-6 py-10 text-center text-slate-500">
              Aucun dossier trouvé pour ce filtre.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-[700px] w-full border-collapse table-fixed">
                <thead className="bg-slate-50">
                  <tr className="text-left text-sm text-slate-500">
                    <th className="w-[28%] px-5 py-4 font-medium">Entreprise</th>
                    <th className="w-[18%] px-5 py-4 font-medium">SIRET</th>
                    <th className="w-[10%] px-5 py-4 font-medium text-center">Docs</th>
                    <th className="w-[18%] px-5 py-4 font-medium">Statut</th>
                    <th className="w-[14%] px-5 py-4 font-medium">Mis à jour</th>
                    <th className="w-[12%] px-5 py-4 font-medium text-right">Action</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredCases.map((item) => (
                    <tr
                      key={item.id}
                      className="border-t border-slate-100 transition hover:bg-slate-50/70"
                    >
                      <td className="px-5 py-4">
                        <p className="truncate font-semibold text-slate-900">{item.companyName}</p>
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-700 font-mono">{item.siret || "—"}</td>

                      <td className="px-5 py-4 text-center text-sm font-semibold text-slate-900">
                        {item.documents}
                      </td>

                      <td className="px-5 py-4">
                        <StatusBadge
                          label={item.status}
                          variant={getStatusVariant(item.status)}
                        />
                      </td>

                      <td className="px-5 py-4 text-sm text-slate-500 truncate">{item.updatedAt || "—"}</td>

                      <td className="px-5 py-4 text-right whitespace-nowrap">
                        <Link
                          to={`/crm/${item.id}`}
                          className="inline-flex items-center rounded-2xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
                        >
                          Voir
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </SectionCard>
      </div>
    </Layout>
  );
};
