interface BadgeProps {
  variant: "gold" | "jade" | "amber" | "dim";
  children: React.ReactNode;
}

export default function Badge({ variant, children }: BadgeProps) {
  return <span className={`badge badge-${variant}`}>{children}</span>;
}
