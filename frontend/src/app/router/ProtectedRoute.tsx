import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/modules/identity/context/AuthContext";

export default function ProtectedRoute() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Keep expired/suspended tenant users inside the application only for
  // the routes that can be used to resolve billing/subscription access.
  if (
    user &&
    !user.is_platform_admin &&
    ["suspended", "disabled", "cancelled", "expired"].includes(
      (user.tenant_status ?? "").toLowerCase(),
    )
  ) {
    return <Navigate to="/platform/plans" replace />;
  }

  return <Outlet />;
}
