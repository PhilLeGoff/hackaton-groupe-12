export const SectionCard = ({ title, subtitle, rightElement, children, className = "" }) => {
  return (
    <section
      className={`rounded-3xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      {(title || subtitle || rightElement) && (
        <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div>
            {title && <h2 className="text-xl font-semibold text-slate-900">{title}</h2>}
            {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
          </div>

          {rightElement && <div>{rightElement}</div>}
        </div>
      )}

      {children}
    </section>
  );
};