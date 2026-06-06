import type { Project } from "../../types/workspace";
import { MaterialIcon } from "../icons/MaterialIcon";

type Props = {
  projects: Project[];
  activeProjectId: string;
  docCountByProject: Record<string, number>;
  onSelectProject: (id: string) => void;
  onNewSummary: () => void;
  onOpenHistory?: () => void;
  onOpenStats?: () => void;
  statsActive?: boolean;
};

export function ProjectSidebar({
  projects,
  activeProjectId,
  docCountByProject,
  onSelectProject,
  onNewSummary,
  onOpenHistory,
  onOpenStats,
  statsActive = false,
}: Props) {
  return (
    <nav className="hidden h-full w-[260px] shrink-0 flex-col overflow-y-auto custom-scrollbar border-r border-outline-variant bg-surface-container-lowest px-3 pb-8 pt-5 lg:flex">
      <div className="mb-5 px-1">
        <button
          type="button"
          onClick={onNewSummary}
          className="flex w-full items-center justify-center gap-2 rounded-xl bg-primary py-2.5 text-sm font-semibold text-white shadow-sm transition-all duration-200 hover:bg-primary/90 active:scale-[0.97]"
        >
          <MaterialIcon name="add" filled size="sm" />
          Tóm tắt tài liệu mới
        </button>
      </div>

      <div className="flex flex-col gap-0.5">
        <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-outline">
          Dự án
        </p>
        {projects.map((p) => {
          const active = p.id === activeProjectId;
          const count = docCountByProject[p.id] ?? 0;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onSelectProject(p.id)}
              className={`flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-left transition-all duration-150 ${
                active
                  ? "active-project"
                  : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
              }`}
            >
              <MaterialIcon
                name="folder"
                size="sm"
                className={active ? "text-primary" : "text-outline"}
              />
              <span className="flex-1 truncate text-sm font-medium">{p.name}</span>
              {count > 0 ? (
                <span
                  className={`min-w-[1.25rem] rounded-md px-1.5 py-0.5 text-center text-[10px] font-semibold ${
                    active ? "bg-primary/15 text-primary" : "bg-surface-container text-outline"
                  }`}
                >
                  {count}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>

      <div className="mt-6 flex flex-col gap-0.5">
        <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-wider text-outline">
          Công cụ
        </p>
        <button
          type="button"
          onClick={onOpenHistory}
          className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-on-surface-variant transition-all duration-150 hover:bg-surface-container hover:text-on-surface"
        >
          <MaterialIcon name="history" size="sm" className="text-outline" />
          <span className="text-sm font-medium">Lịch sử</span>
        </button>
        <button
          type="button"
          onClick={onOpenStats}
          className={`flex items-center gap-2.5 rounded-lg px-3 py-2 transition-all duration-150 ${
            statsActive
              ? "bg-primary-fixed text-primary"
              : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface"
          }`}
        >
          <MaterialIcon
            name="bar_chart"
            size="sm"
            className={statsActive ? "text-primary" : "text-outline"}
          />
          <span className="text-sm font-medium">Thống kê</span>
        </button>
      </div>
    </nav>
  );
}
