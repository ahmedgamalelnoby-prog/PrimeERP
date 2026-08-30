import { ArrowUpLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { quickActions } from "../../data/dashboard.data";

export default function QuickActions() {
  const navigate = useNavigate();

  return (
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold">
          إجراءات سريعة
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          الوصول السريع إلى العمليات المتكررة
        </p>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {quickActions.map((action) => {
          const Icon = action.icon;

          return (
            <button
              key={action.id}
              type="button"
              onClick={() => navigate(action.path)}
              className="group flex items-center gap-3 rounded-xl border p-4 text-right transition-colors hover:bg-muted/60"
            >
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>

              <div className="min-w-0 flex-1">
                <p className="font-medium">
                  {action.title}
                </p>

                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {action.description}
                </p>
              </div>

              <ArrowUpLeft className="h-4 w-4 text-muted-foreground transition-transform group-hover:-translate-x-1" />
            </button>
          );
        })}
      </div>
    </section>
  );
}
