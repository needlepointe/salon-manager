import { Tabs } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

type IoniconsName = React.ComponentProps<typeof Ionicons>["name"];

const TABS: { name: string; label: string; icon: IoniconsName; iconActive: IoniconsName }[] = [
  { name: "index", label: "Dashboard", icon: "grid-outline", iconActive: "grid" },
  { name: "appointments", label: "Schedule", icon: "calendar-outline", iconActive: "calendar" },
  { name: "clients", label: "Clients", icon: "people-outline", iconActive: "people" },
  { name: "leads", label: "Leads", icon: "sparkles-outline", iconActive: "sparkles" },
  { name: "chat", label: "Chat", icon: "chatbubble-outline", iconActive: "chatbubble" },
];

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: "#7c3aed",
        tabBarInactiveTintColor: "#9ca3af",
        tabBarStyle: {
          borderTopWidth: 1,
          borderTopColor: "#e5e7eb",
          backgroundColor: "#ffffff",
          paddingBottom: 4,
        },
        headerStyle: { backgroundColor: "#ffffff" },
        headerShadowVisible: false,
        headerTitleStyle: { fontWeight: "600", color: "#111827" },
      }}
    >
      {TABS.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{
            title: tab.label,
            tabBarIcon: ({ focused, color, size }) => (
              <Ionicons
                name={focused ? tab.iconActive : tab.icon}
                size={size}
                color={color}
              />
            ),
          }}
        />
      ))}
    </Tabs>
  );
}
