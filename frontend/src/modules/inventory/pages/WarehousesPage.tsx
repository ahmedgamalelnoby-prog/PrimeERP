import { useEffect, useState } from "react";

interface Warehouse {
  id: number;
  company_id: number;
  branch_id: number | null;
  code: string;
  name: string;
  is_central: boolean;
  is_active: boolean;
}

export default function WarehousesPage() {
  const [companyId, setCompanyId] = useState("1");
  const [branchId, setBranchId] = useState("");
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);

  useEffect(() => {
    const params = new URLSearchParams({ company_id: companyId });
    if (branchId) params.set("branch_id", branchId);
    fetch(`/api/v1/inventory/warehouses?${params.toString()}`)
      .then((response) => (response.ok ? response.json() : []))
      .then(setWarehouses)
      .catch(() => setWarehouses([]));
  }, [companyId, branchId]);

  return (
    <section className="space-y-6 p-6" dir="rtl">
      <header>
        <h1 className="text-2xl font-bold">المخازن</h1>
        <p className="mt-1 text-sm text-muted-foreground">المخزن المركزي يظهر مع مخازن الفرع عند اختيار الفرع.</p>
      </header>
      <div className="flex gap-3">
        <input className="rounded-lg border bg-background px-3 py-2" value={companyId} onChange={(e) => setCompanyId(e.target.value)} placeholder="Company ID" />
        <input className="rounded-lg border bg-background px-3 py-2" value={branchId} onChange={(e) => setBranchId(e.target.value)} placeholder="Branch ID (اختياري)" />
      </div>
      <div className="overflow-hidden rounded-2xl border bg-card">
        <table className="w-full text-right text-sm">
          <thead><tr className="border-b"><th className="p-3">الكود</th><th className="p-3">المخزن</th><th className="p-3">النطاق</th><th className="p-3">الحالة</th></tr></thead>
          <tbody>
            {warehouses.map((warehouse) => (
              <tr key={warehouse.id} className="border-b last:border-0">
                <td className="p-3 font-medium">{warehouse.code}</td>
                <td className="p-3">{warehouse.name}</td>
                <td className="p-3">{warehouse.is_central ? "مركزي — كل الفروع" : `فرع ${warehouse.branch_id}`}</td>
                <td className="p-3">{warehouse.is_active ? "نشط" : "غير نشط"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
