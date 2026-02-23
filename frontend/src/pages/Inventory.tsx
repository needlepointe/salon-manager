import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, AlertTriangle, Sparkles, Package } from "lucide-react";
import {
  inventoryApi,
  type InventoryProduct,
  type ProductCreate,
} from "../api/inventory";
import Modal from "../components/ui/Modal";
import Spinner from "../components/ui/Spinner";
import EmptyState from "../components/ui/EmptyState";

function ProductForm({
  onSubmit,
  loading,
}: {
  onSubmit: (data: ProductCreate) => void;
  loading?: boolean;
}) {
  const [form, setForm] = useState<ProductCreate>({
    name: "",
    category: "",
    supplier_name: "",
    unit_cost: undefined,
    retail_price: undefined,
    current_stock: 0,
    stock_unit: "units",
    reorder_threshold: 5,
    reorder_quantity: 10,
  });
  const set = <K extends keyof ProductCreate>(k: K, v: ProductCreate[K]) =>
    setForm((p) => ({ ...p, [k]: v }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
      className="space-y-4"
    >
      <div>
        <label className="label">Product Name *</label>
        <input
          className="input"
          value={form.name}
          onChange={(e) => set("name", e.target.value)}
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Category</label>
          <input
            className="input"
            value={form.category ?? ""}
            onChange={(e) => set("category", e.target.value)}
          />
        </div>
        <div>
          <label className="label">Supplier</label>
          <input
            className="input"
            value={form.supplier_name ?? ""}
            onChange={(e) => set("supplier_name", e.target.value)}
          />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="label">Current Stock</label>
          <input
            className="input"
            type="number"
            value={form.current_stock}
            onChange={(e) => set("current_stock", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="label">Reorder At</label>
          <input
            className="input"
            type="number"
            value={form.reorder_threshold}
            onChange={(e) => set("reorder_threshold", Number(e.target.value))}
          />
        </div>
        <div>
          <label className="label">Reorder Qty</label>
          <input
            className="input"
            type="number"
            value={form.reorder_quantity}
            onChange={(e) => set("reorder_quantity", Number(e.target.value))}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Unit Cost ($)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            value={form.unit_cost ?? ""}
            onChange={(e) =>
              set("unit_cost", e.target.value ? Number(e.target.value) : undefined)
            }
          />
        </div>
        <div>
          <label className="label">Retail Price ($)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            value={form.retail_price ?? ""}
            onChange={(e) =>
              set("retail_price", e.target.value ? Number(e.target.value) : undefined)
            }
          />
        </div>
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={loading} className="btn-primary">
          {loading && <Spinner size="sm" />}
          Add Product
        </button>
      </div>
    </form>
  );
}

export default function Inventory() {
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [reorderAdvice, setReorderAdvice] = useState<unknown>(null);
  const [advisorLoading, setAdvisorLoading] = useState(false);

  const { data: products, isLoading } = useQuery({
    queryKey: ["inventory"],
    queryFn: () => inventoryApi.listProducts(),
  });

  const { data: alerts } = useQuery({
    queryKey: ["inventory-alerts"],
    queryFn: inventoryApi.getAlerts,
    refetchInterval: 300_000,
  });

  const createMutation = useMutation({
    mutationFn: inventoryApi.createProduct,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["inventory"] });
      setShowAdd(false);
    },
  });

  const runAdvisor = async () => {
    setAdvisorLoading(true);
    try {
      const data = await inventoryApi.getReorderAdvice();
      setReorderAdvice(data);
    } finally {
      setAdvisorLoading(false);
    }
  };

  const lowStockCount = (alerts as InventoryProduct[] | null)?.length ?? 0;

  return (
    <div className="space-y-4">
      {lowStockCount > 0 && (
        <div className="flex items-center gap-2 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          {lowStockCount} product{lowStockCount !== 1 ? "s" : ""} below reorder
          threshold
        </div>
      )}

      <div className="flex gap-3 justify-between">
        <button onClick={() => setShowAdd(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Add Product
        </button>
        <button
          onClick={runAdvisor}
          disabled={advisorLoading}
          className="btn-secondary"
        >
          {advisorLoading ? <Spinner size="sm" /> : <Sparkles className="w-4 h-4" />}
          AI Reorder Advice
        </button>
      </div>

      {reorderAdvice && (
        <div className="card">
          <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600" />
            AI Reorder Recommendations
          </h3>
          <pre className="text-xs text-gray-700 whitespace-pre-wrap">
            {JSON.stringify(reorderAdvice, null, 2)}
          </pre>
        </div>
      )}

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : !products || products.length === 0 ? (
          <EmptyState
            icon={<Package className="w-12 h-12" />}
            title="No products yet"
            description="Add your first inventory item"
            action={
              <button onClick={() => setShowAdd(true)} className="btn-primary">
                <Plus className="w-4 h-4" /> Add Product
              </button>
            }
          />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Product
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Category
                </th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">
                  Stock
                </th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">
                  Threshold
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Supplier
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Cost
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {products.map((p) => {
                const isLow = p.current_stock <= p.reorder_threshold;
                return (
                  <tr key={p.id} className={isLow ? "bg-yellow-50" : "hover:bg-gray-50"}>
                    <td className="px-4 py-3">
                      <div className="font-medium text-gray-900">{p.name}</div>
                      {isLow && (
                        <span className="badge badge-yellow">Low stock</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {p.category ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-center font-medium">
                      {p.current_stock} {p.stock_unit}
                    </td>
                    <td className="px-4 py-3 text-center text-gray-500">
                      {p.reorder_threshold}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {p.supplier_name ?? "—"}
                    </td>
                    <td className="px-4 py-3 text-gray-700">
                      {p.unit_cost != null ? `$${p.unit_cost}` : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Product">
        <ProductForm
          onSubmit={(data) => createMutation.mutate(data)}
          loading={createMutation.isPending}
        />
      </Modal>
    </div>
  );
}
