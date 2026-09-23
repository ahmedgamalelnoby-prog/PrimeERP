import {
  LogOut,
  Menu,
  UserCircle,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { useAuth } from "@/modules/identity/context/AuthContext";

interface AppHeaderProps {
  onMenuClick: () => void;
}

export default function AppHeader({
  onMenuClick,
}: AppHeaderProps) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const userName =
    user?.full_name ||
    user?.name ||
    user?.username ||
    user?.email ||
    "مستخدم";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b bg-background/95 px-4 backdrop-blur lg:px-6">
      <div className="flex items-center gap-3">
        <Button
          type="button"
          variant="outline"
          size="icon"
          className="lg:hidden"
          onClick={onMenuClick}
          aria-label="فتح القائمة"
        >
          <Menu className="h-5 w-5" />
        </Button>

        <div>
          <h2 className="text-lg font-semibold">
            {user?.tenant_name || "PrimeERP"}
          </h2>
          <p className="hidden text-xs text-muted-foreground sm:block">
            مساحة عمل PrimeERP
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <div className="hidden text-left sm:block">
          <p className="text-sm font-medium">
            {userName}
          </p>

          <p className="text-xs text-muted-foreground">
            {user?.role_name || user?.role || "مستخدم النظام"}
          </p>
        </div>

        <UserCircle className="h-8 w-8 text-muted-foreground" />

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={handleLogout}
        >
          <LogOut className="ml-2 h-4 w-4" />
          تسجيل الخروج
        </Button>
      </div>
    </header>
  );
}