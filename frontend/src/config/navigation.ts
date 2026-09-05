/**
 * Global Navigation Configuration for DealFlow360 (Phases 042 & 043).
 * 
 * Centralized, typed navigation metadata with role-aware visibility filtering.
 * Role-aware navigation is a UX convenience — backend permission middleware
 * and object-level authorization remain the true security boundary.
 */
import {
  LayoutDashboard,
  Users,
  FileText,
  Percent,
  Warehouse,
  ShieldCheck,
  Settings,
  LucideIcon,
} from "lucide-react";

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: string;
  roles?: string[]; // If omitted or empty, visible to all authenticated roles
  section: "overview" | "deal_governance" | "operations" | "system";
  isPlaceholder?: boolean;
  description?: string;
}

export interface NavSection {
  id: "overview" | "deal_governance" | "operations" | "system";
  title: string;
  items: NavItem[];
}

export const NAVIGATION_ITEMS: NavItem[] = [
  // Overview
  {
    id: "dashboard",
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
    section: "overview",
    roles: [], // All authenticated users
    description: "Operational system status and governance summary",
  },
  // Deal Governance
  {
    id: "customers",
    label: "Customers",
    href: "/customers",
    icon: Users,
    section: "deal_governance",
    roles: ["Sales Representative", "Sales Manager", "Finance", "Admin"],
    isPlaceholder: false,
    description: "Customer accounts, profile details, tier assignment & history",
  },
  {
    id: "quotations",
    label: "Quotations",
    href: "/quotations",
    icon: FileText,
    section: "deal_governance",
    roles: ["Sales Representative", "Sales Manager", "Admin", "Customer Portal"],
    isPlaceholder: true,
    description: "Quotation drafts, line items, and lifecycle management",
  },
  {
    id: "discount_governance",
    label: "Discount Governance",
    href: "/governance",
    icon: Percent,
    section: "deal_governance",
    roles: ["Sales Manager", "Finance", "Admin"],
    isPlaceholder: true,
    description: "Margin thresholds, approval chains, and policy compliance",
  },
  // Operations
  {
    id: "warehouses",
    label: "Warehouses & Logistics",
    href: "/warehouses",
    icon: Warehouse,
    section: "operations",
    roles: ["Operations", "Admin"],
    isPlaceholder: true,
    description: "Inventory allocation facilities and fulfillment tracking",
  },
  // System
  {
    id: "audit_logs",
    label: "Audit Logs",
    href: "/audit-logs",
    icon: ShieldCheck,
    section: "system",
    roles: ["Admin", "Sales Manager", "Finance"],
    isPlaceholder: true,
    description: "Immutable security events and deal governance audit trail",
  },
  {
    id: "settings",
    label: "System Settings",
    href: "/settings",
    icon: Settings,
    section: "system",
    roles: ["Admin"],
    isPlaceholder: true,
    description: "Organization parameters and enterprise administration",
  },
];

/**
 * Filter navigation items based on current authenticated user's assigned roles (Phase 043).
 * If user is Admin, they have system-level access to all navigation.
 * Otherwise, items are visible only if the user possesses at least one matching role.
 */
export function filterNavItems(items: NavItem[], userRoles: string[] = []): NavItem[] {
  const isAdmin = userRoles.includes("Admin");
  return items.filter((item) => {
    if (!item.roles || item.roles.length === 0) return true;
    if (isAdmin) return true;
    return item.roles.some((role) => userRoles.includes(role));
  });
}

/**
 * Group filtered navigation items into structured semantic sections.
 */
export function getNavSections(userRoles: string[] = []): NavSection[] {
  const allowedItems = filterNavItems(NAVIGATION_ITEMS, userRoles);

  const sections: { id: NavSection["id"]; title: string }[] = [
    { id: "overview", title: "Overview" },
    { id: "deal_governance", title: "Deal Governance" },
    { id: "operations", title: "Operations" },
    { id: "system", title: "System & Governance" },
  ];

  return sections
    .map((sec) => ({
      id: sec.id,
      title: sec.title,
      items: allowedItems.filter((item) => item.section === sec.id),
    }))
    .filter((sec) => sec.items.length > 0);
}
