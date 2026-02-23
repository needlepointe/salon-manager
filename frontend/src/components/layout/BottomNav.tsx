import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  CalendarDays,
  Users,
  Sparkles,
  Package,
  MessageSquare,
  Heart,
  BarChart3,
} from "lucide-react";

const tabs = [
  { to: "/dashboard", label: "Home", icon: LayoutDashboard },
  { to: "/appointments", label: "Schedule", icon: CalendarDays },
  { to: "/clients", label: "Clients", icon: Users },
  { to: "/leads", label: "Leads", icon: Sparkles },
  { to: "/inventory", label: "Stock", icon: Package },
  { to: "/chat", label: "Chat", icon: MessageSquare },
  { to: "/aftercare", label: "Care", icon: Heart },
  { to: "/reports", label: "Reports", icon: BarChart3 },
];

export default function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white border-t border-gray-200 safe-area-pb">
      <div className="flex overflow-x-auto scrollbar-none">
        {tabs.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center min-w-[4rem] flex-1 py-2 px-1 text-center transition-colors ${
                isActive
                  ? "text-brand-600"
                  : "text-gray-400"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon className={`w-5 h-5 ${isActive ? "text-brand-600" : "text-gray-400"}`} />
                <span className="text-[10px] mt-0.5 font-medium leading-tight">{label}</span>
              </>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
