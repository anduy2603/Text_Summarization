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
    <nav className="fixed bottom-0 left-0 z-50 flex w-full items-center justify-around rounded-t-xl border-t border-outline-variant bg-surface px-4 py-2 shadow-lg lg:hidden">
      {items.map((item) => {
        const isActive = active === item.id;
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onChange(item.id)}
            className={`flex flex-col items-center justify-center rounded-xl px-4 py-1 transition-colors ${
              isActive
                ? "bg-primary-container text-on-primary-container"
                : "text-on-surface-variant"
            }`}
          >
            <MaterialIcon name={item.icon} size="sm" />
            <span className="text-xs font-medium">{item.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
