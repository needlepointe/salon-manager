import { useLocation } from "react-router-dom";
import { Bell } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { dashboardApi } from "../../api/dashboard";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/appointments": "Appointments",
  "/clients": "Clients",
  "/leads": "Extension Leads",
  "/inventory": "Inventory",
  "/chat": "Chat FAQ",
  "/aftercare": "Aftercare",
  "/reports": "Reports",
};

export default function TopBar() {
  const { pathname } = useLocation();
  const title = PAGE_TITLES[pathname] ?? "Salon Manager";

  const { data: alertsData } = useQuery({
    queryKey: ["dashboard-alerts"],
    queryFn: dashboardApi.getAlerts,
    refetchInterval: 60_000,
  });

  const alertCount = alertsData?.total ?? 0;

  return (
    <header className="h-14 md:h-16 bg-white border-b border-gray-200 flex items-center justify-between px-4 md:px-6">
      <h1 className="text-lg md:text-xl font-semibold text-gray-900">{title}</h1>

      <div className="flex items-center gap-2">
        <button className="relative p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-100 transition-colors">
          <Bell className="w-5 h-5" />
          {alertCount > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
              {alertCount > 9 ? "9+" : alertCount}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
