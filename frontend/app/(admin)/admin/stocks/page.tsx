"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  PaginatedResponse,
  StockResponse,
  StockCreate,
  StockUpdate,
} from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useState } from "react";

function StockFormDialog({
  stock,
  open,
  onOpenChange,
}: {
  stock: StockResponse | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const queryClient = useQueryClient();
  const isEdit = stock !== null;

  const [form, setForm] = useState({
    symbol: stock?.symbol || "",
    name: stock?.name || "",
    exchange: stock?.exchange || "NSE",
    bse_code: stock?.bse_code || "",
    sector: stock?.sector || "",
    industry: stock?.industry || "",
    is_active: stock?.is_active ?? true,
  });

  const createMutation = useMutation({
    mutationFn: (data: StockCreate) =>
      api.post<StockResponse>("/admin/stocks", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-stocks"] });
      onOpenChange(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: (data: StockUpdate) =>
      api.patch<StockResponse>(`/admin/stocks/${stock!.id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-stocks"] });
      onOpenChange(false);
    },
  });

  const handleSave = () => {
    if (isEdit) {
      const body: StockUpdate = {};
      if (form.name !== stock.name) body.name = form.name;
      if ((form.bse_code || undefined) !== (stock.bse_code || undefined))
        body.bse_code = form.bse_code || undefined;
      if ((form.sector || undefined) !== (stock.sector || undefined))
        body.sector = form.sector || undefined;
      if ((form.industry || undefined) !== (stock.industry || undefined))
        body.industry = form.industry || undefined;
      if (form.is_active !== stock.is_active) body.is_active = form.is_active;

      if (Object.keys(body).length === 0) {
        onOpenChange(false);
        return;
      }
      updateMutation.mutate(body);
    } else {
      const body: StockCreate = {
        symbol: form.symbol,
        name: form.name,
        exchange: form.exchange,
      };
      if (form.bse_code) body.bse_code = form.bse_code;
      if (form.sector) body.sector = form.sector;
      if (form.industry) body.industry = form.industry;
      createMutation.mutate(body);
    }
  };

  const isPending = createMutation.isPending || updateMutation.isPending;
  const isError = createMutation.isError || updateMutation.isError;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Stock" : "Create Stock"}</DialogTitle>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="symbol">Symbol</Label>
              <Input
                id="symbol"
                value={form.symbol}
                onChange={(e) =>
                  setForm({ ...form, symbol: e.target.value.toUpperCase() })
                }
                disabled={isEdit}
                placeholder="e.g. RELIANCE"
              />
            </div>
            <div>
              <Label htmlFor="exchange">Exchange</Label>
              <Input
                id="exchange"
                value={form.exchange}
                onChange={(e) =>
                  setForm({ ...form, exchange: e.target.value })
                }
                disabled={isEdit}
                placeholder="NSE"
              />
            </div>
          </div>
          <div>
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Reliance Industries Ltd"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="sector">Sector</Label>
              <Input
                id="sector"
                value={form.sector}
                onChange={(e) => setForm({ ...form, sector: e.target.value })}
              />
            </div>
            <div>
              <Label htmlFor="industry">Industry</Label>
              <Input
                id="industry"
                value={form.industry}
                onChange={(e) =>
                  setForm({ ...form, industry: e.target.value })
                }
              />
            </div>
          </div>
          <div>
            <Label htmlFor="bse_code">BSE Code</Label>
            <Input
              id="bse_code"
              value={form.bse_code}
              onChange={(e) => setForm({ ...form, bse_code: e.target.value })}
            />
          </div>
          {isEdit && (
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_active"
                checked={form.is_active}
                onChange={(e) =>
                  setForm({ ...form, is_active: e.target.checked })
                }
                className="h-4 w-4"
              />
              <Label htmlFor="is_active">Active</Label>
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={isPending}>
            {isPending ? "Saving..." : isEdit ? "Save Changes" : "Create"}
          </Button>
        </DialogFooter>
        {isError && (
          <p className="text-destructive text-sm mt-2">
            Failed to {isEdit ? "update" : "create"} stock.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}

export default function StockManagementPage() {
  const [cursor, setCursor] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingStock, setEditingStock] = useState<StockResponse | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["admin-stocks", cursor],
    queryFn: () => {
      const params: Record<string, string> = {};
      if (cursor) params.cursor = cursor;
      return api.get<PaginatedResponse<StockResponse>>(
        "/admin/stocks",
        params,
      );
    },
  });

  return (
    <div className="container mx-auto max-w-5xl py-8 px-4">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Stock Management</h1>
        <Button onClick={() => setShowCreate(true)}>Create Stock</Button>
      </div>

      {isLoading && <p className="text-muted-foreground">Loading...</p>}
      {error && <p className="text-destructive">Failed to load stocks.</p>}

      {data && data.items.length === 0 && (
        <p className="text-muted-foreground">No stocks found.</p>
      )}

      {/* Stock Table */}
      {data && data.items.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left">
                <th className="pb-2 font-medium">Symbol</th>
                <th className="pb-2 font-medium">Name</th>
                <th className="pb-2 font-medium">Exchange</th>
                <th className="pb-2 font-medium">Sector</th>
                <th className="pb-2 font-medium">Active</th>
                <th className="pb-2 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((stock) => (
                <tr key={stock.id} className="border-b">
                  <td className="py-2 font-mono">{stock.symbol}</td>
                  <td className="py-2">{stock.name}</td>
                  <td className="py-2">{stock.exchange}</td>
                  <td className="py-2 text-muted-foreground">
                    {stock.sector || "-"}
                  </td>
                  <td className="py-2">
                    <Badge variant={stock.is_active ? "default" : "secondary"}>
                      {stock.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="py-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setEditingStock(stock)}
                    >
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.has_more && (
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => setCursor(data.next_cursor)}
        >
          Load More
        </Button>
      )}

      {/* Create Dialog */}
      {showCreate && (
        <StockFormDialog
          stock={null}
          open={showCreate}
          onOpenChange={(open) => {
            if (!open) setShowCreate(false);
          }}
        />
      )}

      {/* Edit Dialog */}
      {editingStock && (
        <StockFormDialog
          stock={editingStock}
          open={!!editingStock}
          onOpenChange={(open) => {
            if (!open) setEditingStock(null);
          }}
        />
      )}
    </div>
  );
}
