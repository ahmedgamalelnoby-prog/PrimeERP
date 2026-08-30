import { recentActivities } from "../../data/dashboard.data";

const statusClasses = {
  success: "bg-emerald-500",
  warning: "bg-amber-500",
  info: "bg-blue-500",
  danger: "bg-red-500",
};

export default function RecentActivities() {
  return (
    <section className="rounded-2xl border bg-card p-5 shadow-sm">
      <div>
        <h2 className="text-lg font-semibold">
          آخر الأنشطة
        </h2>

        <p className="mt-1 text-sm text-muted-foreground">
          أحدث العمليات المسجلة على النظام
        </p>
      </div>

      <div className="mt-5 space-y-1">
        {recentActivities.map((activity) => (
          <div
            key={activity.id}
            className="flex gap-3 rounded-xl p-3 transition-colors hover:bg-muted/50"
          >
            <div className="pt-2">
              <span
                className={[
                  "block h-2.5 w-2.5 rounded-full",
                  statusClasses[activity.status],
                ].join(" ")}
              />
            </div>

            <div className="min-w-0 flex-1">
              <p className="text-sm font-medium">
                {activity.title}
              </p>

              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                {activity.description}
              </p>
            </div>

            <time className="shrink-0 text-xs text-muted-foreground">
              {activity.time}
            </time>
          </div>
        ))}
      </div>
    </section>
  );
}
