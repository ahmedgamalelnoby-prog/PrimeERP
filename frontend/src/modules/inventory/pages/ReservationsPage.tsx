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

  const load = () => {
    const params = new URLSearchParams({ company_id: companyId });
    client.get<Reservation[]>("/inventory/reservations", { params: Object.fromEntries(params) })
      .then((response) => setReservations(response.data))
      .catch(() => setReservations([]));
  };

  useEffect(load, [companyId]);

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
      <div className="overflow-hidden rounded-2xl border bg-card">
        <table className="w-full text-right text-sm">
          <thead><tr className="border-b"><th className="p-3">الصنف</th><th className="p-3">الموقع</th><th className="p-3">الكمية</th><th className="p-3">المصدر</th><th className="p-3">الحالة</th></tr></thead>
          <tbody>
            {reservations.map((reservation) => (
              <tr key={reservation.id} className="border-b last:border-0">
                <td className="p-3">{reservation.item_id}</td>
                <td className="p-3">{reservation.location_id}</td>
                <td className="p-3 font-medium">{reservation.quantity}</td>
                <td className="p-3">{reservation.source_module} / {reservation.source_entity} / {reservation.source_id}</td>
                <td className="p-3">{reservation.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
