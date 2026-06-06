import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  apiOk: boolean | null;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSettings: () => void;
  onCompare?: () => void;
};

export function TopNavBar({ apiOk, searchQuery, onSearchChange, onSettings, onCompare }: Props) {
  return (
    <header className="fixed top-0 left-0 z-50 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface-container-lowest px-4 md:px-8">
      <div className="flex items-center gap-6 md:gap-8">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <MaterialIcon name="summarize" size="sm" className="text-white" />
          </div>
          <span className="text-[1.05rem] font-bold tracking-tight text-on-surface">VietSum</span>
        </div>
        <nav className="hidden items-center gap-1 md:flex">
          <a
            href="#"
            className="rounded-lg px-3 py-1.5 text-sm font-semibold text-primary transition-colors hover:bg-primary-container/40"
            onClick={(e) => e.preventDefault()}
          >
            Tài liệu
          </a>
          {onCompare && (
            <button
              type="button"
              onClick={onCompare}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface active:scale-[0.97]"
            >
              <MaterialIcon name="compare" size="sm" />
              So sánh Engine
            </button>
          )}
        </nav>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        {apiOk === false ? (
          <span className="rounded-md bg-error/10 px-2.5 py-1 text-xs font-medium text-error">
            Offline
          </span>
        ) : null}
        <div className="relative hidden sm:block">
          <MaterialIcon
            name="search"
            className="absolute left-3 top-1/2 -translate-y-1/2 text-outline"
            size="sm"
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Tìm tài liệu..."
            className="w-44 rounded-lg border border-outline-variant bg-surface-container-lowest py-1.5 pl-9 pr-4 text-sm transition-colors focus:border-primary/40 focus:outline-none focus:ring-2 focus:ring-primary/15 md:w-56"
          />
        </div>
        <button
          type="button"
          className="rounded-lg p-1.5 text-on-surface-variant transition-colors hover:bg-surface-container hover:text-on-surface active:scale-[0.95]"
          aria-label="Cài đặt"
          onClick={onSettings}
        >
          <MaterialIcon name="settings" size="sm" />
        </button>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg border border-outline-variant bg-primary-container text-xs font-bold text-on-primary-container"
          title="VietSum"
        >
          VS
        </div>
      </div>
    </header>
  );
}
