import api from "./client";

export interface InventoryProduct {
  id: number;
  sku?: string;
  name: string;
  category?: string;
  supplier_name?: string;
  unit_cost?: number;
  retail_price?: number;
  current_stock: number;
  stock_unit: string;
  reorder_threshold: number;
  reorder_quantity: number;
  is_active: boolean;
  last_ordered_at?: string;
}

export interface ProductCreate {
  sku?: string;
  name: string;
  category?: string;
  supplier_name?: string;
  supplier_sku?: string;
  supplier_contact?: string;
  unit_cost?: number;
  retail_price?: number;
  current_stock?: number;
  stock_unit?: string;
  reorder_threshold?: number;
  reorder_quantity?: number;
}

export interface PurchaseOrder {
  id: number;
  status: "draft" | "sent" | "received" | "cancelled";
  supplier_name: string;
  ai_generated: boolean;
  items_json: unknown[];
  total_cost?: number;
  ordered_at?: string;
  received_at?: string;
  created_at: string;
}

export const inventoryApi = {
  listProducts: (params?: { category?: string; low_stock?: boolean }) =>
    api
      .get<InventoryProduct[]>("/inventory/products", { params })
      .then((r) => r.data),

  getProduct: (id: number) =>
    api.get<InventoryProduct>(`/inventory/products/${id}`).then((r) => r.data),

  createProduct: (data: ProductCreate) =>
    api.post<InventoryProduct>("/inventory/products", data).then((r) => r.data),

  updateProduct: (id: number, data: Partial<ProductCreate>) =>
    api
      .put<InventoryProduct>(`/inventory/products/${id}`, data)
      .then((r) => r.data),

  adjustStock: (
    id: number,
    data: { transaction_type: string; quantity_change: number; notes?: string }
  ) =>
    api
      .post(`/inventory/products/${id}/adjust`, data)
      .then((r) => r.data),

  getAlerts: () => api.get("/inventory/alerts").then((r) => r.data),

  getReorderAdvice: () =>
    api.post("/inventory/reorder-advice").then((r) => r.data),

  listOrders: () =>
    api.get<PurchaseOrder[]>("/inventory/purchase-orders").then((r) => r.data),

  createOrder: (data: {
    supplier_name: string;
    items_json: unknown[];
    ai_generated?: boolean;
  }) =>
    api
      .post<PurchaseOrder>("/inventory/purchase-orders", data)
      .then((r) => r.data),

  updateOrder: (id: number, data: Partial<PurchaseOrder>) =>
    api
      .put<PurchaseOrder>(`/inventory/purchase-orders/${id}`, data)
      .then((r) => r.data),
};
