import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import timeGridPlugin from "@fullcalendar/timegrid";
import interactionPlugin from "@fullcalendar/interaction";
import { Plus, CheckCircle, XCircle } from "lucide-react";
import {
  appointmentsApi,
  type Appointment,
  type AppointmentCreate,
} from "../api/appointments";
import { clientsApi } from "../api/clients";
import Modal from "../components/ui/Modal";
import Spinner from "../components/ui/Spinner";
import { format } from "date-fns";

const STATUS_COLORS: Record<string, string> = {
  scheduled: "#7c3aed",
  completed: "#16a34a",
  cancelled: "#9ca3af",
  no_show: "#dc2626",
  needs_review: "#f59e0b",
};

function BookingForm({
  onSubmit,
  loading,
}: {
  onSubmit: (data: AppointmentCreate) => void;
  loading?: boolean;
}) {
  const { data: clients } = useQuery({
    queryKey: ["clients"],
    queryFn: () => clientsApi.list(),
  });

  const [form, setForm] = useState<AppointmentCreate>({
    client_id: 0,
    service_type: "",
    duration_minutes: 60,
    start_datetime: "",
    price: undefined,
    notes: "",
    deposit_paid: false,
  });

  const set = <K extends keyof AppointmentCreate>(
    k: K,
    v: AppointmentCreate[K]
  ) => setForm((p) => ({ ...p, [k]: v }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
      className="space-y-4"
    >
      <div>
        <label className="label">Client *</label>
        <select
          className="input"
          value={form.client_id}
          onChange={(e) => set("client_id", Number(e.target.value))}
          required
        >
          <option value={0}>Select client...</option>
          {clients?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.full_name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label className="label">Service *</label>
        <input
          className="input"
          value={form.service_type}
          onChange={(e) => set("service_type", e.target.value)}
          placeholder="e.g. Tape-in Extensions"
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Start Date & Time *</label>
          <input
            className="input"
            type="datetime-local"
            value={form.start_datetime}
            onChange={(e) => set("start_datetime", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Duration (minutes)</label>
          <input
            className="input"
            type="number"
            value={form.duration_minutes}
            onChange={(e) => set("duration_minutes", Number(e.target.value))}
            min={15}
            step={15}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Price ($)</label>
          <input
            className="input"
            type="number"
            step="0.01"
            value={form.price ?? ""}
            onChange={(e) =>
              set("price", e.target.value ? Number(e.target.value) : undefined)
            }
          />
        </div>
        <div className="flex items-end pb-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={form.deposit_paid}
              onChange={(e) => set("deposit_paid", e.target.checked)}
              className="rounded border-gray-300 text-brand-600"
            />
            <span className="text-sm text-gray-700">Deposit paid</span>
          </label>
        </div>
      </div>
      <div>
        <label className="label">Notes</label>
        <textarea
          className="input min-h-[60px]"
          value={form.notes ?? ""}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={loading} className="btn-primary">
          {loading && <Spinner size="sm" />}
          Book Appointment
        </button>
      </div>
    </form>
  );
}

export default function Appointments() {
  const qc = useQueryClient();
  const [showBook, setShowBook] = useState(false);
  const [selected, setSelected] = useState<Appointment | null>(null);

  const { data: appointments, isLoading } = useQuery({
    queryKey: ["appointments"],
    queryFn: () => appointmentsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: appointmentsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["appointments"] });
      setShowBook(false);
    },
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) => appointmentsApi.complete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["appointments"] });
      setSelected(null);
    },
  });

  const cancelMutation = useMutation({
    mutationFn: (id: number) => appointmentsApi.cancel(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["appointments"] });
      setSelected(null);
    },
  });

  const events =
    appointments?.map((a) => ({
      id: String(a.id),
      title: `${a.client_name ?? `Client #${a.client_id}`} — ${a.service_type}`,
      start: a.start_datetime,
      end: a.end_datetime,
      backgroundColor: STATUS_COLORS[a.status] ?? "#7c3aed",
      borderColor: STATUS_COLORS[a.status] ?? "#7c3aed",
      extendedProps: a,
    })) ?? [];

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowBook(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Book Appointment
        </button>
      </div>

      <div className="card p-4">
        {isLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : (
          <FullCalendar
            plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
            initialView="timeGridWeek"
            headerToolbar={{
              left: "prev,next today",
              center: "title",
              right: "dayGridMonth,timeGridWeek,timeGridDay",
            }}
            events={events}
            eventClick={(info) => {
              setSelected(info.event.extendedProps as Appointment);
            }}
            height="auto"
            slotMinTime="07:00:00"
            slotMaxTime="21:00:00"
          />
        )}
      </div>

      {/* Book modal */}
      <Modal
        open={showBook}
        onClose={() => setShowBook(false)}
        title="Book Appointment"
        size="lg"
      >
        <BookingForm
          onSubmit={(data) => createMutation.mutate(data)}
          loading={createMutation.isPending}
        />
      </Modal>

      {/* Detail modal */}
      {selected && (
        <Modal
          open
          onClose={() => setSelected(null)}
          title="Appointment Details"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-gray-500">Client</p>
                <p className="font-medium">
                  {selected.client_name ?? `#${selected.client_id}`}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Service</p>
                <p className="font-medium">{selected.service_type}</p>
              </div>
              <div>
                <p className="text-gray-500">Start</p>
                <p className="font-medium">
                  {format(new Date(selected.start_datetime), "MMM d, h:mm a")}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Status</p>
                <span
                  className="badge"
                  style={{
                    backgroundColor:
                      STATUS_COLORS[selected.status] + "20",
                    color: STATUS_COLORS[selected.status],
                  }}
                >
                  {selected.status}
                </span>
              </div>
              {selected.price != null && (
                <div>
                  <p className="text-gray-500">Price</p>
                  <p className="font-medium">${selected.price}</p>
                </div>
              )}
            </div>

            {selected.status === "scheduled" && (
              <div className="flex gap-3 pt-2">
                <button
                  className="btn-primary flex-1"
                  onClick={() => completeMutation.mutate(selected.id)}
                  disabled={completeMutation.isPending}
                >
                  <CheckCircle className="w-4 h-4" />
                  Mark Complete
                </button>
                <button
                  className="btn-danger flex-1"
                  onClick={() => cancelMutation.mutate(selected.id)}
                  disabled={cancelMutation.isPending}
                >
                  <XCircle className="w-4 h-4" />
                  Cancel
                </button>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
