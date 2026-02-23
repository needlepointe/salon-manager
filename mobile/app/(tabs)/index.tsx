import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  StyleSheet,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { dashboardApi, appointmentsApi, aftercareApi } from "../../src/api";
import { format } from "date-fns";

function StatCard({
  label,
  value,
  color = "#7c3aed",
}: {
  label: string;
  value: string | number;
  color?: string;
}) {
  return (
    <View style={[styles.statCard, { borderLeftColor: color }]}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

export default function DashboardScreen() {
  const qc = useQueryClient();

  const { data: stats, isLoading: statsLoading, refetch: refetchStats } =
    useQuery({ queryKey: ["stats"], queryFn: dashboardApi.getStats });

  const { data: today, refetch: refetchToday } = useQuery({
    queryKey: ["today"],
    queryFn: dashboardApi.getToday,
  });

  const { data: alertsData, refetch: refetchAlerts } = useQuery({
    queryKey: ["alerts"],
    queryFn: dashboardApi.getAlerts,
  });

  const { data: pending, refetch: refetchPending } = useQuery({
    queryKey: ["aftercare-pending"],
    queryFn: aftercareApi.getPending,
  });

  const refreshing = statsLoading;
  const onRefresh = () => {
    refetchStats();
    refetchToday();
    refetchAlerts();
    refetchPending();
  };

  const completeMutation = useMutation({
    mutationFn: (id: number) => appointmentsApi.complete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["today"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });

  const sendD3 = useMutation({
    mutationFn: (id: number) => aftercareApi.sendD3(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aftercare-pending"] }),
  });

  const sendW2 = useMutation({
    mutationFn: (id: number) => aftercareApi.sendW2(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["aftercare-pending"] }),
  });

  const alerts = alertsData?.alerts ?? [];
  const todayAppts = today?.appointments ?? [];
  const pendingItems = pending ?? [];

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#7c3aed" />
      }
    >
      {/* Stats */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>This Month</Text>
        <View style={styles.statsGrid}>
          <StatCard
            label="Revenue"
            value={`$${Number(stats?.revenue_this_month ?? 0).toFixed(0)}`}
            color="#16a34a"
          />
          <StatCard label="Appointments" value={stats?.appointments_this_month ?? 0} />
          <StatCard
            label="Lapsed Clients"
            value={stats?.lapsed_clients ?? 0}
            color="#f59e0b"
          />
          <StatCard label="Active Leads" value={stats?.active_leads ?? 0} />
        </View>
      </View>

      {/* Alerts */}
      {alerts.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Action Items{" "}
            <Text style={styles.badge}>{alerts.length}</Text>
          </Text>
          {alerts.map((alert: { type: string; severity: string; title: string; detail: string }, i: number) => (
            <View
              key={i}
              style={[
                styles.alertRow,
                alert.severity === "error" && styles.alertError,
                alert.severity === "warning" && styles.alertWarning,
              ]}
            >
              <Ionicons
                name={
                  alert.severity === "error"
                    ? "alert-circle"
                    : alert.severity === "warning"
                    ? "warning"
                    : "information-circle"
                }
                size={18}
                color={
                  alert.severity === "error"
                    ? "#dc2626"
                    : alert.severity === "warning"
                    ? "#d97706"
                    : "#2563eb"
                }
              />
              <View style={{ flex: 1, marginLeft: 8 }}>
                <Text style={styles.alertTitle}>{alert.title}</Text>
                <Text style={styles.alertDetail}>{alert.detail}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Today's Schedule */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>
          Today — {format(new Date(), "EEE MMM d")}
        </Text>
        {todayAppts.length === 0 ? (
          <Text style={styles.emptyText}>No appointments today</Text>
        ) : (
          todayAppts.map(
            (appt: {
              id: number;
              client_name: string;
              service_type: string;
              start_time: string;
              status: string;
            }) => (
              <View key={appt.id} style={styles.apptRow}>
                <View style={styles.apptTime}>
                  <Text style={styles.apptTimeText}>{appt.start_time}</Text>
                </View>
                <View style={{ flex: 1 }}>
                  <Text style={styles.apptClient}>{appt.client_name}</Text>
                  <Text style={styles.apptService}>{appt.service_type}</Text>
                </View>
                {appt.status === "scheduled" && (
                  <TouchableOpacity
                    style={styles.doneBtn}
                    onPress={() => completeMutation.mutate(appt.id)}
                  >
                    <Ionicons name="checkmark" size={16} color="#ffffff" />
                  </TouchableOpacity>
                )}
                {appt.status === "completed" && (
                  <View style={styles.completedBadge}>
                    <Text style={styles.completedText}>Done</Text>
                  </View>
                )}
              </View>
            )
          )
        )}
      </View>

      {/* Aftercare Due */}
      {pendingItems.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Aftercare Due</Text>
          {pendingItems.map(
            (item: {
              id: number;
              type: string;
              client_name: string;
              service_type: string;
            }) => (
              <View key={`${item.id}-${item.type}`} style={styles.aftercareRow}>
                <View style={{ flex: 1 }}>
                  <Text style={styles.apptClient}>{item.client_name}</Text>
                  <Text style={styles.apptService}>{item.service_type}</Text>
                </View>
                <View
                  style={[
                    styles.typeBadge,
                    item.type === "d3" ? styles.d3Badge : styles.w2Badge,
                  ]}
                >
                  <Text style={styles.typeBadgeText}>
                    {item.type === "d3" ? "Day 3" : "Week 2"}
                  </Text>
                </View>
                <TouchableOpacity
                  style={styles.sendBtn}
                  onPress={() =>
                    item.type === "d3"
                      ? sendD3.mutate(item.id)
                      : sendW2.mutate(item.id)
                  }
                >
                  <Ionicons name="send" size={14} color="#ffffff" />
                </TouchableOpacity>
              </View>
            )
          )}
        </View>
      )}

      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  section: { margin: 16, marginBottom: 0 },
  sectionTitle: { fontSize: 15, fontWeight: "600", color: "#111827", marginBottom: 10 },
  badge: {
    backgroundColor: "#fecaca",
    color: "#dc2626",
    fontSize: 12,
    paddingHorizontal: 6,
    borderRadius: 8,
  },
  statsGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  statCard: {
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 14,
    flex: 1,
    minWidth: "45%",
    borderLeftWidth: 3,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: { fontSize: 24, fontWeight: "700", color: "#111827" },
  statLabel: { fontSize: 12, color: "#6b7280", marginTop: 2 },
  alertRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    backgroundColor: "#eff6ff",
    borderRadius: 10,
    padding: 12,
    marginBottom: 8,
  },
  alertError: { backgroundColor: "#fef2f2" },
  alertWarning: { backgroundColor: "#fffbeb" },
  alertTitle: { fontSize: 13, fontWeight: "600", color: "#111827" },
  alertDetail: { fontSize: 12, color: "#6b7280", marginTop: 2 },
  emptyText: { fontSize: 13, color: "#9ca3af", textAlign: "center", padding: 16 },
  apptRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  apptTime: {
    width: 56,
    alignItems: "center",
    marginRight: 10,
  },
  apptTimeText: { fontSize: 13, fontWeight: "600", color: "#7c3aed" },
  apptClient: { fontSize: 14, fontWeight: "600", color: "#111827" },
  apptService: { fontSize: 12, color: "#6b7280", marginTop: 1 },
  doneBtn: {
    backgroundColor: "#7c3aed",
    borderRadius: 8,
    width: 32,
    height: 32,
    alignItems: "center",
    justifyContent: "center",
  },
  completedBadge: {
    backgroundColor: "#dcfce7",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
  },
  completedText: { fontSize: 12, color: "#16a34a", fontWeight: "600" },
  aftercareRow: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderRadius: 12,
    padding: 12,
    marginBottom: 8,
    shadowColor: "#000",
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 1,
  },
  typeBadge: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, marginRight: 8 },
  d3Badge: { backgroundColor: "#dbeafe" },
  w2Badge: { backgroundColor: "#ede9fe" },
  typeBadgeText: { fontSize: 11, fontWeight: "600", color: "#1e40af" },
  sendBtn: {
    backgroundColor: "#7c3aed",
    borderRadius: 8,
    width: 30,
    height: 30,
    alignItems: "center",
    justifyContent: "center",
  },
});
