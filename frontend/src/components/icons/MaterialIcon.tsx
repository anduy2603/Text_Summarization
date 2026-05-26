type Props = {
  name: string;
  className?: string;
  filled?: boolean;
  size?: "sm" | "md" | "lg";
};

const sizeClass = {
  sm: "text-[18px]",
  md: "text-2xl",
  lg: "text-3xl",
};

export function MaterialIcon({ name, className = "", filled = false, size = "md" }: Props) {
  return (
    <span
      className={`material-symbols-outlined leading-none ${sizeClass[size]} ${className}`}
      style={filled ? { fontVariationSettings: "'FILL' 1" } : undefined}
      aria-hidden
    >
      {name}
    </span>
  );
}
