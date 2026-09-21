export default function DashboardFooter() {
  return (
    <footer className="mt-auto border-t border-slate-200 bg-white/60 px-4 py-4 sm:px-5 lg:px-8">
      <div className="flex flex-col items-center justify-between gap-2 text-xs text-slate-400 sm:flex-row">
        <div className="flex items-center gap-2">
          <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-gradient-to-br from-brand-400 to-brand-600 text-[9px] font-bold text-white">
            K
          </span>
          <span>
            Kalyan Admin &copy; {new Date().getFullYear()} &mdash; Educational simulator, virtual credits only.
          </span>
        </div>
        <span className="font-mono text-[11px] text-slate-300">v2.0.0</span>
      </div>
    </footer>
  );
}
