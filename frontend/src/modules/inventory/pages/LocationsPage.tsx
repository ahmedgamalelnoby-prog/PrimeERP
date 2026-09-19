import { useEffect, useState } from "react";
import client from "@/shared/api/client";

interface Location {
  id: number;
  warehouse_id: number;
  parent_id: number | null;
  code: string;
  name: string;
  location_type: string;
  is_virtual: boolean;
  is_active: boolean;
}

export default function LocationsPage() {
  const [companyId, setCompanyId] = useState(() => localStorage.getItem("company_id") || "");
  const [warehouseId, setWarehouseId] = useState("");
  const [locations, setLocations] = useState<Location[]>([]);

  useEffect(() => {
    if (!warehouseId) return;
    const params = new URLSearchParams({ company_id: companyId, warehouse_id: warehouseId });
    client.get<Location[]>("/inventory/locations", { params: Object.fromEntries(params) })
      .then((response) => setLocations(response.data))
      .catch(() => setLocations([]));
  }, [companyId, warehouseId]);

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">مواقع التخزين</h1>
        <p className="mt-1 text-sm text-muted-foreground">هيكل هرمي داخل المخزن لدعم الاستلام والتخزين والشحن والمناطق الخاصة.</p>
      </header>
      <div className="flex gap-3">
        <input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={(e) => setCompanyId(e.target.value)} placeholder="Company ID" />
        <input className="rounded-lg border bg-background px-3 py-2" value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} placeholder="Warehouse ID" />
      </div>
      <div className="overflow-hidden rounded-2xl border bg-card">
        <table className="w-full text-right text-sm">
          <thead><tr className="border-b"><th className="p-3">الكود</th><th className="p-3">الموقع</th><th className="p-3">النوع</th><th className="p-3">الأب</th></tr></thead>
          <tbody>
            {locations.map((location) => (
              <tr key={location.id} className="border-b last:border-0">
                <td className="p-3 font-medium">{location.code}</td>
                <td className="p-3">{location.name}</td>
                <td className="p-3">{location.location_type}</td>
                <td className="p-3">{location.parent_id ?? "رئيسي"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
