import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { AlertTriangle, Info, AlertCircle, ChevronRight } from "lucide-react";
import { dashboardApi } from "../../api/dashboard";
import Spinner from "../ui/Spinner";

interface Alert {
  type: string;
  severity: "info" | "warning" | "error";
  title: string;
  detail: string;
  link: string;
  count?: number;
  item_id?: number;
}

const severityIcon = {
  info: <Info className="w-4 h-4 text-blue-500" />,
  warning: <AlertTriangle className="w-4 h-4 text-yellow-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
};

const severityBg = {
  info: "bg-blue-50 border-blue-100",
  warning: "bg-yellow-50 border-yellow-100",
  error: "bg-red-50 border-red-100",
};

export default function AlertsPanel() {
  const navigate = useNavigate();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-alerts"],
    queryFn: dashboardApi.getAlerts,
    refetchInterval: 60_000,
  });

  if (isLoading)
    return (
      <div className="card flex items-center justify-center h-48">
        <Spinner />
      </div>
    );

  const alerts: Alert[] = data?.alerts ?? [];

  return (
    <div className="card">
      <h2 className="text-base font-semibold text-gray-900 mb-4">
        Action Items
        {alerts.length > 0 && (
          <span className="ml-2 badge badge-red">{alerts.length}</span>
        )}
      </h2>

      {alerts.length === 0 ? (
        <p className="text-sm text-gray-500 py-8 text-center">
          No action items right now
        </p>
      ) : (
        <div className="space-y-2">
          {alerts.map((alert, i) => (
            <button
              key={i}
              onClick={() => navigate(alert.link)}
              className={`w-full flex items-start gap-3 p-3 rounded-lg border text-left hover:opacity-90 transition-opacity ${severityBg[alert.severity]}`}
            >
              <span className="mt-0.5 flex-shrink-0">
                {severityIcon[alert.severity]}
              </span>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900">
                  {alert.title}
                </p>
                <p className="text-xs text-gray-500 mt-0.5 truncate">
                  {alert.detail}
                </p>
              </div>
              <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
