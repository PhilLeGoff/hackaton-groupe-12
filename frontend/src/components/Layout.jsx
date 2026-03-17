import { Header } from "./Header";

export const Layout = ({ children, title, subtitle, className = "", noHeader = false }) => {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      {!noHeader && <Header />}

      <main className="mx-auto w-full max-w-7xl px-6 py-8 md:py-10">
        {(title || subtitle) && (
          <div className="mb-8">
            {title && <h1 className="text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">{title}</h1>}
            {subtitle && <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600 md:text-base">{subtitle}</p>}
          </div>
        )}

        <div className={className}>{children}</div>
      </main>
    </div>
  );
};