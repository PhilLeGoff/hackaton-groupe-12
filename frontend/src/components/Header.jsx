import { Link, NavLink } from "react-router-dom";

export const Header = () => {
  const navClass = ({ isActive }) =>
    `rounded-full px-4 py-2 text-sm font-medium transition ${
      isActive
        ? "bg-slate-900 text-white shadow-sm"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white shadow-sm">
            DF
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">DocuFlow AI</p>
            <p className="text-xs text-slate-500">CRM & conformité documentaire</p>
          </div>
        </Link>

        <nav className="hidden items-center gap-2 md:flex">
          <NavLink to="/" className={navClass}>
            Accueil
          </NavLink>
          <NavLink to="/crm" className={navClass}>
            CRM
          </NavLink>
          <NavLink to="/crm/1" className={navClass}>
            Dossiers
          </NavLink>
          <NavLink to="/compliance/1" className={navClass}>
            Conformité
          </NavLink>
        </nav>
      </div>
    </header>
  );
};