import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { CalendarDays, Clock } from "lucide-react";
import { appointmentsApi } from "../../api/appointments";
import Spinner from "../ui/Spinner";

export default function UpcomingAppointments() {
  const { data: appointments, isLoading } = useQuery({
    queryKey: ["appointments-upcoming"],
    queryFn: appointmentsApi.getUpcoming,
    refetchInterval: 60_000,
  });

  if (isLoading)
    return (
      <div className="card flex items-center justify-center h-48">
        <Spinner />
      </div>
    );

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <CalendarDays className="w-5 h-5 text-brand-600" />
        <h2 className="text-base font-semibold text-gray-900">
          Upcoming (7 days)
        </h2>
      </div>

      {!appointments || appointments.length === 0 ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          No upcoming appointments
        </p>
      ) : (
        <div className="space-y-3">
          {appointments.slice(0, 8).map((appt) => (
            <div
              key={appt.id}
              className="flex items-center gap-3 p-3 rounded-lg bg-gray-50"
            >
              <div className="flex-shrink-0 w-10 text-center">
                <div className="text-xs font-medium text-brand-600">
                  {format(new Date(appt.start_datetime), "EEE")}
                </div>
                <div className="text-lg font-bold text-gray-900 leading-tight">
                  {format(new Date(appt.start_datetime), "d")}
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {appt.client_name ?? `Client #${appt.client_id}`}
                </p>
                <p className="text-xs text-gray-500">{appt.service_type}</p>
              </div>
              <div className="flex items-center gap-1 text-xs text-gray-500">
                <Clock className="w-3 h-3" />
                {format(new Date(appt.start_datetime), "h:mm a")}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
