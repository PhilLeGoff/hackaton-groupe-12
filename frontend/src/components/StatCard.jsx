export const StatCard = ({ title, value, subtitle, badge, badgeVariant = "default" }) => {
  const badgeStyles = {
    default: "bg-slate-100 text-slate-700",
    success: "bg-emerald-100 text-emerald-700",
    warning: "bg-amber-100 text-amber-700",
    danger: "bg-rose-100 text-rose-700",
    info: "bg-sky-100 text-sky-700",
  };

  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold text-slate-900">{value}</p>
        </div>

        {badge && (
          <div
            className={`rounded-2xl px-3 py-2 text-sm font-semibold ${badgeStyles[badgeVariant]}`}
          >
            {badge}
          </div>
        )}
      </div>

      {subtitle && <p className="mt-4 text-sm text-slate-600">{subtitle}</p>}
    </div>
  );
};