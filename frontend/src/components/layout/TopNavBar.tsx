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
    <header className="fixed top-0 left-0 z-50 flex h-16 w-full items-center justify-between border-b border-outline-variant bg-surface px-4 md:px-8">
      <div className="flex items-center gap-6 md:gap-8">
        <span className="text-xl font-bold text-primary">VietSum</span>
        <nav className="hidden items-center gap-6 md:flex">
          <a
            href="#"
            className="border-b-2 border-primary py-5 text-sm font-medium tracking-wide text-primary"
            onClick={(e) => e.preventDefault()}
          >
            Tài liệu
          </a>
          {onCompare && (
            <button
              type="button"
              onClick={onCompare}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
            >
              <MaterialIcon name="compare" size="sm" />
              So sánh Engine
            </button>
          )}
        </nav>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        {apiOk === false ? (
          <span className="rounded-full bg-error/10 px-2 py-0.5 text-xs font-medium text-error">
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
            placeholder="Tìm kiếm tài liệu..."
            className="w-48 rounded-full border border-outline-variant bg-surface-container-low py-2 pl-10 pr-4 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 md:w-64"
          />
        </div>
        <button
          type="button"
          className="rounded-full p-2 text-on-surface-variant transition-colors hover:bg-surface-container"
          aria-label="Cài đặt"
          onClick={onSettings}
        >
          <MaterialIcon name="settings" size="sm" />
        </button>
        <div
          className="ml-1 flex h-8 w-8 items-center justify-center rounded-full border border-outline-variant bg-primary-container text-xs font-bold text-on-primary-container"
          title="Người dùng"
        >
          VS
        </div>
      </div>
    </header>
  );
}
