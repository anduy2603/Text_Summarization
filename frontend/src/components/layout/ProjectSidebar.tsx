import { useRef, useState } from "react";
import { DEFAULT_PROJECT_ID } from "../../constants";
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
  onCreateProject: (name: string) => void;
  onRenameProject: (id: string, name: string) => void;
  onDeleteProject: (id: string) => void;
};

function InlineInput({
  defaultValue = "",
  placeholder,
  onConfirm,
  onCancel,
}: {
  defaultValue?: string;
  placeholder: string;
  onConfirm: (value: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(defaultValue);
  const ref = useRef<HTMLInputElement>(null);

  const confirm = () => {
    const trimmed = value.trim();
    if (trimmed) onConfirm(trimmed);
    else onCancel();
  };

  return (
    <div className="flex items-center gap-1 rounded-lg border border-primary/40 bg-surface-container-lowest px-2 py-1">
      <input
        ref={ref}
        autoFocus
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") confirm();
          if (e.key === "Escape") onCancel();
        }}
        placeholder={placeholder}
        className="min-w-0 flex-1 bg-transparent text-sm font-medium text-on-surface outline-none placeholder:text-outline"
        maxLength={40}
      />
      <button
        type="button"
        onClick={confirm}
        className="shrink-0 rounded p-0.5 text-primary hover:bg-primary/10"
        aria-label="Xác nhận"
      >
        <MaterialIcon name="check" size="sm" />
      </button>
      <button
        type="button"
        onClick={onCancel}
        className="shrink-0 rounded p-0.5 text-on-surface-variant hover:bg-surface-container"
        aria-label="Hủy"
      >
        <MaterialIcon name="close" size="sm" />
      </button>
    </div>
  );
}

export function ProjectSidebar({
  projects,
  activeProjectId,
  docCountByProject,
  onSelectProject,
  onNewSummary,
  onOpenHistory,
  onOpenStats,
  statsActive = false,
  onCreateProject,
  onRenameProject,
  onDeleteProject,
}: Props) {
  const [creating, setCreating] = useState(false);
  const [renamingId, setRenamingId] = useState<string | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

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

      {/* Projects section */}
      <div className="flex flex-col gap-0.5">
        <div className="mb-1.5 flex items-center justify-between px-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-outline">Dự án</p>
          <button
            type="button"
            onClick={() => { setCreating(true); setRenamingId(null); }}
            className="rounded p-0.5 text-outline transition-colors hover:bg-surface-container hover:text-primary"
            title="Tạo dự án mới"
            aria-label="Tạo dự án mới"
          >
            <MaterialIcon name="add" size="sm" />
          </button>
        </div>

        {projects.map((p) => {
          const active = p.id === activeProjectId;
          const count = docCountByProject[p.id] ?? 0;
          const isDefault = p.id === DEFAULT_PROJECT_ID;
          const renaming = renamingId === p.id;

          if (renaming) {
            return (
              <div key={p.id} className="px-1 py-0.5">
                <InlineInput
                  defaultValue={p.name}
                  placeholder="Tên dự án"
                  onConfirm={(name) => {
                    onRenameProject(p.id, name);
                    setRenamingId(null);
                  }}
                  onCancel={() => setRenamingId(null)}
                />
              </div>
            );
          }

          return (
            <div
              key={p.id}
              className="group relative"
              onMouseEnter={() => setHoveredId(p.id)}
              onMouseLeave={() => setHoveredId(null)}
            >
              <button
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
                {/* doc count — hide when action buttons visible */}
                {count > 0 && hoveredId !== p.id ? (
                  <span
                    className={`min-w-[1.25rem] rounded-md px-1.5 py-0.5 text-center text-[10px] font-semibold ${
                      active ? "bg-primary/15 text-primary" : "bg-surface-container text-outline"
                    }`}
                  >
                    {count}
                  </span>
                ) : null}
              </button>

              {/* Action buttons on hover */}
              {hoveredId === p.id ? (
                <div className="absolute right-1 top-1/2 flex -translate-y-1/2 items-center gap-0.5">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setRenamingId(p.id);
                      setCreating(false);
                    }}
                    className="rounded p-1 text-on-surface-variant transition-colors hover:bg-surface-container hover:text-primary"
                    title="Đổi tên"
                    aria-label="Đổi tên dự án"
                  >
                    <MaterialIcon name="edit" size="sm" />
                  </button>
                  {!isDefault ? (
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteProject(p.id);
                      }}
                      className="rounded p-1 text-on-surface-variant transition-colors hover:bg-red-50 hover:text-red-500"
                      title="Xóa dự án"
                      aria-label="Xóa dự án"
                    >
                      <MaterialIcon name="delete" size="sm" />
                    </button>
                  ) : null}
                </div>
              ) : null}
            </div>
          );
        })}

        {/* Inline create input */}
        {creating ? (
          <div className="mt-1 px-1">
            <InlineInput
              placeholder="Tên dự án mới"
              onConfirm={(name) => {
                onCreateProject(name);
                setCreating(false);
              }}
              onCancel={() => setCreating(false)}
            />
          </div>
        ) : null}
      </div>

      {/* Tools section */}
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
