import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
  label: string;
  value: number | null;
  icon: LucideIcon;
  color: string; // tailwind bg class
  loading?: boolean;
}

export function StatCard({ label, value, icon: Icon, color, loading }: StatCardProps) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`${color} p-3 rounded-xl text-white shrink-0`}>
          <Icon size={22} />
        </div>
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          {loading ? (
            <Skeleton className="h-7 w-16 mt-1" />
          ) : (
            <p className="text-2xl font-bold text-gray-800">
              {value?.toLocaleString("ar-SA") ?? "—"}
            </p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
