import type { ReactElement } from "react";
import { Navigate } from "react-router-dom";

import { useAuth } from "../../modules/identity";

import { ROUTES } from "./routes";

interface PublicRouteProps {
  children: ReactElement;
}

export default function PublicRoute({
  children,
}: PublicRouteProps) {
  const {
    isAuthenticated,
    isLoading,
  } = useAuth();

  if (isLoading) {
    return <div>جارٍ تحميل النظام...</div>;
  }

  if (isAuthenticated) {
    return (
      <Navigate
        to={ROUTES.DASHBOARD}
        replace
      />
    );
  }

  return children;
}