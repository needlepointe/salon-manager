import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, Plus, UserX, Phone, Mail, RefreshCw } from "lucide-react";
import { clientsApi, type Client, type ClientCreate } from "../api/clients";
import Modal from "../components/ui/Modal";
import Spinner from "../components/ui/Spinner";
import EmptyState from "../components/ui/EmptyState";
import { format } from "date-fns";

function ClientForm({
  initial,
  onSubmit,
  loading,
}: {
  initial?: Partial<ClientCreate>;
  onSubmit: (data: ClientCreate) => void;
  loading?: boolean;
}) {
  const [form, setForm] = useState<ClientCreate>({
    full_name: initial?.full_name ?? "",
    phone: initial?.phone ?? "",
    email: initial?.email ?? "",
    notes: initial?.notes ?? "",
  });
  const set = (k: keyof ClientCreate, v: string) =>
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
        <label className="label">Full Name *</label>
        <input
          className="input"
          value={form.full_name}
          onChange={(e) => set("full_name", e.target.value)}
          required
        />
      </div>
      <div>
        <label className="label">Phone *</label>
        <input
          className="input"
          value={form.phone}
          onChange={(e) => set("phone", e.target.value)}
          placeholder="+1XXXXXXXXXX"
          required
        />
      </div>
      <div>
        <label className="label">Email</label>
        <input
          className="input"
          type="email"
          value={form.email ?? ""}
          onChange={(e) => set("email", e.target.value)}
        />
      </div>
      <div>
        <label className="label">Notes</label>
        <textarea
          className="input min-h-[80px]"
          value={form.notes ?? ""}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>
      <div className="flex justify-end gap-3 pt-2">
        <button type="submit" disabled={loading} className="btn-primary">
          {loading ? <Spinner size="sm" /> : null}
          {initial?.full_name ? "Save Changes" : "Add Client"}
        </button>
      </div>
    </form>
  );
}

function ClientRow({
  client,
  onOpen,
  onOutreach,
}: {
  client: Client;
  onOpen: () => void;
  onOutreach: () => void;
}) {
  return (
    <tr className="hover:bg-gray-50 cursor-pointer" onClick={onOpen}>
      <td className="px-4 py-3">
        <div className="font-medium text-gray-900">{client.full_name}</div>
        {client.is_lapsed && (
          <span className="badge badge-yellow mt-0.5">Lapsed</span>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Phone className="w-3 h-3" />
          {client.phone}
        </div>
        {client.email && (
          <div className="flex items-center gap-1 mt-0.5">
            <Mail className="w-3 h-3" />
            {client.email}
          </div>
        )}
      </td>
      <td className="px-4 py-3 text-sm text-gray-700 text-center">
        {client.total_visits}
      </td>
      <td className="px-4 py-3 text-sm text-gray-700">
        ${Number(client.total_spent).toFixed(0)}
      </td>
      <td className="px-4 py-3 text-sm text-gray-500">
        {client.last_visit_date
          ? format(new Date(client.last_visit_date), "MMM d, yyyy")
          : "—"}
      </td>
      <td className="px-4 py-3">
        {client.is_lapsed && (
          <button
            className="btn-secondary text-xs py-1 px-2"
            onClick={(e) => {
              e.stopPropagation();
              onOutreach();
            }}
          >
            <RefreshCw className="w-3 h-3" />
            Re-engage
          </button>
        )}
      </td>
    </tr>
  );
}

export default function Clients() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState<Client | null>(null);

  const { data: clients, isLoading } = useQuery({
    queryKey: ["clients", search],
    queryFn: () => clientsApi.list({ search }),
  });

  const addMutation = useMutation({
    mutationFn: clientsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      setShowAdd(false);
    },
  });

  const outreachMutation = useMutation({
    mutationFn: clientsApi.sendOutreach,
    onSuccess: () => alert("Outreach SMS sent!"),
  });

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            className="input pl-9"
            placeholder="Search clients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <button onClick={() => setShowAdd(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Add Client
        </button>
      </div>

      <div className="card p-0 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : !clients || clients.length === 0 ? (
          <EmptyState
            icon={<UserX className="w-12 h-12" />}
            title="No clients yet"
            description="Add your first client to get started"
            action={
              <button onClick={() => setShowAdd(true)} className="btn-primary">
                <Plus className="w-4 h-4" /> Add Client
              </button>
            }
          />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Name
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Contact
                </th>
                <th className="px-4 py-3 text-center font-medium text-gray-600">
                  Visits
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Spent
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Last Visit
                </th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {clients.map((c) => (
                <ClientRow
                  key={c.id}
                  client={c}
                  onOpen={() => setSelected(c)}
                  onOutreach={() => outreachMutation.mutate(c.id)}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Add modal */}
      <Modal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        title="Add Client"
      >
        <ClientForm
          onSubmit={(data) => addMutation.mutate(data)}
          loading={addMutation.isPending}
        />
      </Modal>

      {/* Detail modal */}
      {selected && (
        <Modal
          open
          onClose={() => setSelected(null)}
          title={selected.full_name}
          size="lg"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-gray-500">Phone</p>
                <p className="font-medium">{selected.phone}</p>
              </div>
              <div>
                <p className="text-gray-500">Email</p>
                <p className="font-medium">{selected.email || "—"}</p>
              </div>
              <div>
                <p className="text-gray-500">Total visits</p>
                <p className="font-medium">{selected.total_visits}</p>
              </div>
              <div>
                <p className="text-gray-500">Total spent</p>
                <p className="font-medium">
                  ${Number(selected.total_spent).toFixed(2)}
                </p>
              </div>
            </div>
            {selected.notes && (
              <div>
                <p className="text-sm text-gray-500">Notes</p>
                <p className="text-sm mt-1 whitespace-pre-wrap">
                  {selected.notes}
                </p>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
