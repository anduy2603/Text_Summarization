import { MaterialIcon } from "../icons/MaterialIcon";

export type MobileTab = "home" | "history" | "projects" | "profile";

type Props = {
  active: MobileTab;
  onChange: (tab: MobileTab) => void;
};

export function MobileBottomNav({ active, onChange }: Props) {
  const items: { id: MobileTab; icon: string; label: string }[] = [
    { id: "home", icon: "home", label: "Trang chủ" },
    { id: "history", icon: "history", label: "Lịch sử" },
    { id: "projects", icon: "folder", label: "Tài liệu" },
    { id: "profile", icon: "person", label: "Cá nhân" },
  ];

  return (
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-center justify-around border-t border-outline-variant bg-surface-container-lowest px-2 py-1.5 lg:hidden">
      {items.map((item) => {
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            className={`flex flex-1 flex-col items-center justify-center gap-0.5 rounded-xl py-1.5 transition-all duration-150 active:scale-[0.95] ${
              isActive
                ? "text-primary"
                : "text-on-surface-variant hover:text-on-surface"
            }`}
          >
            <div className={`rounded-xl px-4 py-1 transition-colors ${isActive ? "bg-primary-container" : ""}`}>
              <MaterialIcon name={item.icon} size="sm" />
            </div>
            <span className={`text-[10px] font-semibold ${isActive ? "text-primary" : "text-on-surface-variant"}`}>
              {item.label}
            </span>
          </button>
        );
      })}
    </nav>
  );
}
