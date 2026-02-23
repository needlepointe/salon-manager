import { useQuery } from "@tanstack/react-query";
import {
  DollarSign,
  CalendarCheck,
  Users,
  UserX,
  Sparkles,
  CalendarDays,
} from "lucide-react";
import StatsCard from "../components/dashboard/StatsCard";
import AlertsPanel from "../components/dashboard/AlertsPanel";
import UpcomingAppointments from "../components/dashboard/UpcomingAppointments";
import { dashboardApi } from "../api/dashboard";

export default function Dashboard() {
  const { data: stats } = useQuery({
    queryKey: ["dashboard-stats"],
    queryFn: dashboardApi.getStats,
    refetchInterval: 60_000,
  });

  return (
    <div className="space-y-6">
      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-3 md:gap-4">
        <StatsCard
          title="Revenue this month"
          value={`$${(stats?.revenue_this_month ?? 0).toFixed(0)}`}
          icon={<DollarSign className="w-5 h-5" />}
          color="green"
        />
        <StatsCard
          title="Appts this month"
          value={stats?.appointments_this_month ?? 0}
          icon={<CalendarCheck className="w-5 h-5" />}
          color="blue"
        />
        <StatsCard
          title="Total clients"
          value={stats?.total_clients ?? 0}
          icon={<Users className="w-5 h-5" />}
          color="purple"
        />
        <StatsCard
          title="Lapsed clients"
          value={stats?.lapsed_clients ?? 0}
          subtitle="90+ days absent"
          icon={<UserX className="w-5 h-5" />}
          color="orange"
        />
        <StatsCard
          title="Active leads"
          value={stats?.active_leads ?? 0}
          icon={<Sparkles className="w-5 h-5" />}
          color="purple"
        />
        <StatsCard
          title="Upcoming (7d)"
          value={stats?.upcoming_7_days ?? 0}
          icon={<CalendarDays className="w-5 h-5" />}
          color="blue"
        />
      </div>

      {/* Lower panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AlertsPanel />
        <UpcomingAppointments />
      </div>
    </div>
  );
}
