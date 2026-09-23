import { ChevronDown, X } from "lucide-react";
import { useAuth } from "@/modules/identity/hooks/useAuth";
import { useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";

import {
  getVisibleNavigationItems,
  isNavigationItemActive,
  type NavigationItem,
} from "@/app/navigation";

interface AppSidebarProps {
  open: boolean;
  onClose: () => void;
}

function NavigationNode({
  item,
  pathname,
  onNavigate,
}: {
  item: NavigationItem;
  pathname: string;
  onNavigate: () => void;
}) {
  const [expanded, setExpanded] = useState(
    isNavigationItemActive(item, pathname),
  );

  useEffect(() => {
    if (isNavigationItemActive(item, pathname)) {
      setExpanded(true);
    }
  }, [item, pathname]);

  const Icon = item.icon;
  const hasChildren = Boolean(item.children?.length);
  const active = isNavigationItemActive(item, pathname);

  if (item.type === "separator") {
    return <div className="my-3 border-t" />;
  }

  if (hasChildren) {
    return (
      <div className="space-y-1">
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className={[
            "flex w-full items-center justify-between rounded-xl px-3 py-2.5",
            "text-sm font-medium transition-colors",
            active
              ? "bg-primary/10 text-primary"
              : "text-foreground hover:bg-muted",
          ].join(" ")}
        >
          <span className="flex min-w-0 items-center gap-3">
            {Icon && <Icon className="h-5 w-5 shrink-0" />}
            <span className="truncate">{item.labelAr}</span>
          </span>
          <ChevronDown
            className={[
              "h-4 w-4 shrink-0 transition-transform",
              expanded ? "rotate-180" : "",
            ].join(" ")}
          />
        </button>

        {expanded && (
          <div className="mr-5 space-y-1 border-r pr-3">
            {item.children?.map((child) => (
              <NavigationNode
                key={child.id}
                item={child}
                pathname={pathname}
                onNavigate={onNavigate}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  if (!item.path) {
    return null;
  }

  return (
    <NavLink
      to={item.path}
      onClick={onNavigate}
      className={({ isActive }) =>
        [
          "flex items-center gap-3 rounded-lg px-3 py-2",
          "text-sm transition-colors",
          isActive
            ? "bg-primary text-primary-foreground shadow-sm"
            : "text-muted-foreground hover:bg-muted hover:text-foreground",
        ].join(" ")
      }
    >
      {Icon && <Icon className="h-4 w-4 shrink-0" />}
      <span className="truncate">{item.labelAr}</span>
      {item.isNew && (
        <span className="mr-auto rounded-full bg-blue-100 px-1.5 py-0.5 text-[9px] font-bold text-blue-700">
          جديد
        </span>
      )}
    </NavLink>
  );
}

export default function AppSidebar({ open, onClose }: AppSidebarProps) {
  const location = useLocation();
  const { user } = useAuth();
  const navigation = getVisibleNavigationItems(user?.enabled_modules ?? [], Boolean(user?.is_platform_admin || user?.is_superuser));
  return (
    <>
      {open && (
        <button
          type="button"
          aria-label="إغلاق القائمة"
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={[
          "fixed right-0 top-0 z-50 h-screen w-72",
          "border-l bg-card shadow-xl",
          "transition-transform duration-300",
          open ? "translate-x-0" : "translate-x-full",
          "lg:translate-x-0",
        ].join(" ")}
      >
        <div className="flex h-16 items-center justify-between border-b px-5">
          <div>
            <h1 className="text-xl font-bold">PrimeERP</h1>
            <p className="text-xs text-muted-foreground">
              Enterprise Resource Planning
            </p>
          </div>

          <button
            type="button"
            className="rounded-lg p-2 transition-colors hover:bg-muted lg:hidden"
            onClick={onClose}
            aria-label="إغلاق القائمة"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="h-[calc(100vh-4rem)] overflow-y-auto p-4">
          <p className="mb-3 px-3 text-xs font-semibold text-muted-foreground">
            القائمة الرئيسية
          </p>
          <div className="space-y-1">
            {navigation.map((item) => (
              <NavigationNode
                key={item.id}
                item={item}
                pathname={location.pathname}
                onNavigate={onClose}
              />
            ))}
          </div>
        </nav>
      </aside>
    </>
  );
}
