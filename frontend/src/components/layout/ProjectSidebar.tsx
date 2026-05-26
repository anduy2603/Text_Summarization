import type { Project } from "../../types/workspace";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  projects: Project[];
  activeProjectId: string;
  docCountByProject: Record<string, number>;
  onSelectProject: (id: string) => void;
  onNewSummary: () => void;
  onOpenHistory?: () => void;
};

export function ProjectSidebar({
  projects,
  activeProjectId,
  docCountByProject,
  onSelectProject,
  onNewSummary,
  onOpenHistory,
}: Props) {
  return (
    <nav className="hidden h-full w-[280px] shrink-0 flex-col overflow-y-auto custom-scrollbar border-r border-outline-variant bg-surface-container-low px-4 pb-8 pt-6 lg:flex">
      <div className="mb-6 px-2">
        <button
          type="button"
          onClick={onNewSummary}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary-container py-3 text-sm font-medium tracking-wide text-on-primary-container transition-all hover:opacity-90 active:scale-95"
        >
          <MaterialIcon name="add" filled size="sm" />
          Tải tệp tóm tắt
        </button>
      </div>

      <div className="flex flex-col gap-1">
        <p className="mb-2 px-3 text-xs font-bold uppercase tracking-wider text-outline">
          Dự án của bạn
        </p>
        {projects.map((p) => {
          const active = p.id === activeProjectId;
          const count = docCountByProject[p.id] ?? 0;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectProject(p.id)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition-all ${
                active
                  ? "active-project rounded-r-lg"
                  : "text-on-surface-variant hover:bg-surface-container-high"
              }`}
            >
              <MaterialIcon name="folder" size="sm" />
              <span className="flex-1 truncate text-sm font-medium">{p.name}</span>
              {count > 0 ? (
                <span className="text-xs text-outline">{count}</span>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="mt-8 flex flex-col gap-1">
        <p className="mb-2 px-3 text-xs font-bold uppercase tracking-wider text-outline">Công cụ</p>
        <button
          type="button"
          onClick={onOpenHistory}
          className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-on-surface-variant transition-all hover:bg-surface-container-high"
        >
          <MaterialIcon name="history" size="sm" />
          <span className="text-sm font-medium">Lịch sử</span>
        </button>
      </div>
    </nav>
  );
}
