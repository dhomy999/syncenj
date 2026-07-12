"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  CalendarClock,
  ScrollText,
  Users,
  BookOpen,
  UserPlus,
  RefreshCcwDot,
} from "lucide-react";

const nav = [
  { href: "/",           label: "الرئيسية",        icon: LayoutDashboard },
  { href: "/jobs",       label: "المهام",           icon: CalendarClock },
  { href: "/logs",       label: "السجلات",         icon: ScrollText },
  { href: "/students",   label: "الطلاب",          icon: Users },
  { href: "/halaqat",    label: "الحلقات",         icon: BookOpen },
  { href: "/recitation", label: "مزامنة التسميع",  icon: RefreshCcwDot },
  { href: "/import",     label: "إضافة طلاب",      icon: UserPlus },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 shrink-0 bg-white border-l border-gray-200 flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-gray-200">
        <span className="text-lg font-bold text-emerald-700">إنجازي</span>
        <span className="text-xs text-gray-400 mr-2 mt-1">أتمتة</span>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors",
                active
                  ? "bg-emerald-50 text-emerald-700 font-semibold"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icon size={18} />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-gray-200 text-xs text-gray-400">
        v1.0.0
      </div>
    </aside>
  );
}
