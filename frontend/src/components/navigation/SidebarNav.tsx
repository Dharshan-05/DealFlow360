"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getNavSections, NavItem } from "@/config/navigation";
import { cn } from "@/lib/utils";

interface SidebarNavProps {
  userRoles?: string[];
  isCollapsed?: boolean;
  onItemClick?: () => void;
}

export function SidebarNav({
  userRoles = [],
  isCollapsed = false,
  onItemClick,
}: SidebarNavProps) {
  const pathname = usePathname();
  const sections = getNavSections(userRoles);

  return (
    <nav className="flex flex-col space-y-6" aria-label="Main Navigation">
      {sections.map((section) => (
        <div key={section.id} className="flex flex-col space-y-1.5">
          {!isCollapsed && (
            <span className="px-3 text-xs font-semibold uppercase tracking-wider text-slate-400">
              {section.title}
            </span>
          )}
          <ul className="space-y-1">
            {section.items.map((item: NavItem) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              return (
                <li key={item.id}>
                  <Link
                    href={item.href}
                    onClick={onItemClick}
                    aria-current={isActive ? "page" : undefined}
                    title={isCollapsed ? item.label : undefined}
                    className={cn(
                      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
                      isActive
                        ? "bg-blue-50 text-primary font-semibold"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
                      isCollapsed && "justify-center px-2"
                    )}
                  >
                    <Icon
                      className={cn("h-4 w-4 shrink-0", isActive ? "text-primary" : "text-slate-500")}
                      aria-hidden="true"
                    />
                    {!isCollapsed && (
                      <div className="flex flex-1 items-center justify-between overflow-hidden">
                        <span className="truncate">{item.label}</span>
                        {item.isPlaceholder && (
                          <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                            Roadmap
                          </span>
                        )}
                      </div>
                    )}
                  </Link>
                </li>
              );
            })}
          </ul>
        </div>
      ))}
    </nav>
  );
}
