import { Badge } from "@/components/ui/badge";
import { useTranslation } from "react-i18next";

interface RoleStatusProps {
  isActive: boolean;
}

export default function RoleStatus({
  isActive,
} : RoleStatusProps) {
  const { t } = useTranslation();
  return (
    <Badge
      variant="secondary"
      className={
        isActive
          ? "bg-emerald-500/10 text-emerald-700 hover:bg-emerald-500/10"
          : "bg-slate-500/10 text-slate-600 hover:bg-slate-500/10"
      }
    >
      <span
        className={[
          "ms-1.5 h-1.5 w-1.5 rounded-full",
          isActive
            ? "bg-emerald-500"
            : "bg-slate-400",
        ].join(" ")}
      />

      {isActive ? t("rolesTable.active") : t("rolesTable.inactive")}
    </Badge>
  );
}