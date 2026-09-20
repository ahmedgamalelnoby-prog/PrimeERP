import { useEffect, useState } from "react";
import client from "@/shared/api/client";

interface Reservation {
  id: number;
  item_id: number;
  location_id: number;
  quantity: string;
  status: string;
  source_module: string;
  source_entity: string;
  source_id: string;
}

export default function ReservationsPage() {
  const [companyId, setCompanyId] = useState(() => localStorage.getItem("company_id") || "");
  const [reservations, setReservations] = useState<Reservation[]>([]);

  const [message, setMessage] = useState("");

  const load = () => {
    const params = new URLSearchParams({ company_id: companyId });
    client.get<Reservation[]>("/inventory/reservations", { params: Object.fromEntries(params) })
      .then((response) => setReservations(response.data))
      .catch(() => setReservations([]));
  };

  useEffect(load, [companyId]);

  const action = async (id: number, kind: "release" | "cancel") => {
    try {
      await client.post(`/inventory/reservations/${id}/${kind}`, undefined, { params: { company_id: companyId } });
      setMessage(kind === "release" ? "تم تحرير الحجز." : "تم إلغاء الحجز.");
      load();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "تعذر تنفيذ العملية");
    }
  };

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">حجوزات المخزون</h1>
        <p className="mt-1 text-sm text-muted-foreground">متابعة الكميات المحجوزة للطلبات والمعاملات مع الحفاظ على On Hand منفصلًا عن Available.</p>
      </header>
      <div className="flex gap-3">
        <input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={(e) => setCompanyId(e.target.value)} placeholder="Company ID" />
        <button className="rounded-lg border px-4 py-2" onClick={load}>تحديث</button>
      </div>
      {message && <div className="rounded-lg border p-3 text-sm">{message}</div>}
      <div className="overflow-hidden rounded-2xl border bg-card">
        <table className="w-full text-right text-sm">
          <thead><tr className="border-b"><th className="p-3">الصنف</th><th className="p-3">الموقع</th><th className="p-3">الكمية</th><th className="p-3">المصدر</th><th className="p-3">الحالة</th><th className="p-3">إجراء</th></tr></thead>
          <tbody>
            {reservations.map((reservation) => (
              <tr key={reservation.id} className="border-b last:border-0">
                <td className="p-3">{reservation.item_id}</td>
                <td className="p-3">{reservation.location_id}</td>
                <td className="p-3 font-medium">{reservation.quantity}</td>
                <td className="p-3">{reservation.source_module} / {reservation.source_entity} / {reservation.source_id}</td>
                <td className="p-3">{reservation.status}</td>
                <td className="p-3 space-x-2 space-x-reverse">
                  {reservation.status === "active" && <>
                    <button className="rounded border px-2 py-1" onClick={() => void action(reservation.id, "release")}>تحرير</button>
                    <button className="rounded border px-2 py-1" onClick={() => void action(reservation.id, "cancel")}>إلغاء</button>
                  </>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
