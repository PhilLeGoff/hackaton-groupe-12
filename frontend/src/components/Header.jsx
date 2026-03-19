import { useState } from "react";
import { Link, NavLink } from "react-router-dom";

export const Header = () => {
  const [mobileOpen, setMobileOpen] = useState(false);

  const navClass = ({ isActive }) =>
    `rounded-full px-4 py-2 text-sm font-medium transition ${
      isActive
        ? "bg-slate-900 text-white shadow-sm"
        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
    }`;

  const mobileNavClass = ({ isActive }) =>
    `block rounded-2xl px-4 py-3 text-sm font-medium transition ${
      isActive
        ? "bg-slate-900 text-white"
        : "text-slate-700 hover:bg-slate-100"
    }`;

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/90 backdrop-blur">
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-6">
        <Link to="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-sm font-bold text-white shadow-sm">
            DS
          </div>
          <div>
            <p className="text-lg font-bold text-slate-900">DocuScan AI</p>
            <p className="text-xs text-slate-500">Traitement documentaire intelligent</p>
          </div>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-2 md:flex">
          <NavLink to="/upload" className={navClass}>
            Dépôt
          </NavLink>
          <NavLink to="/dashboard" className={navClass}>
            Documents
          </NavLink>
          <NavLink to="/crm" className={navClass}>
            Dossiers
          </NavLink>
        </nav>

        {/* Mobile hamburger */}
        <button
          onClick={() => setMobileOpen((prev) => !prev)}
          className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-700 md:hidden"
          aria-label="Ouvrir le menu"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <nav className="border-t border-slate-200 bg-white px-6 pb-4 pt-2 md:hidden">
          <div className="flex flex-col gap-1">
            <NavLink to="/upload" className={mobileNavClass} onClick={() => setMobileOpen(false)}>
              Dépôt
            </NavLink>
            <NavLink to="/dashboard" className={mobileNavClass} onClick={() => setMobileOpen(false)}>
              Documents
            </NavLink>
            <NavLink to="/crm" className={mobileNavClass} onClick={() => setMobileOpen(false)}>
              Dossiers
            </NavLink>
          </div>
        </nav>
      )}
    </header>
  );
};
