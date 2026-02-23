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
import { appointmentsApi } from "../../src/api";
import { format } from "date-fns";

export default function AppointmentsScreen() {
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["upcoming"],
    queryFn: appointmentsApi.getUpcoming,
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) => appointmentsApi.complete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["upcoming"] }),
  });

  const noShowMutation = useMutation({
    mutationFn: (id: number) => appointmentsApi.noShow(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["upcoming"] }),
  });

  const appointments: {
    id: number;
    client_name: string;
    service_type: string;
    start_datetime: string;
    status: string;
    price?: number;
  }[] = data ?? [];

  // Group by date
  const grouped = appointments.reduce<Record<string, typeof appointments>>(
    (acc, appt) => {
      const day = format(new Date(appt.start_datetime), "yyyy-MM-dd");
      if (!acc[day]) acc[day] = [];
      acc[day].push(appt);
      return acc;
    },
    {}
  );

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={isLoading} onRefresh={refetch} tintColor="#7c3aed" />
      }
    >
      {Object.keys(grouped).length === 0 && !isLoading && (
        <View style={styles.empty}>
          <Ionicons name="calendar-outline" size={48} color="#d1d5db" />
          <Text style={styles.emptyText}>No upcoming appointments</Text>
        </View>
      )}

      {Object.entries(grouped).map(([day, appts]) => (
        <View key={day} style={styles.daySection}>
          <Text style={styles.dayHeader}>
            {format(new Date(day), "EEEE, MMMM d")}
          </Text>

          {appts.map((appt) => (
            <View key={appt.id} style={styles.card}>
              <View style={styles.timeCol}>
                <Text style={styles.timeText}>
                  {format(new Date(appt.start_datetime), "h:mm")}
                </Text>
                <Text style={styles.ampm}>
                  {format(new Date(appt.start_datetime), "a")}
                </Text>
              </View>

              <View style={styles.info}>
                <Text style={styles.clientName}>{appt.client_name ?? `Client #${appt.id}`}</Text>
                <Text style={styles.serviceName}>{appt.service_type}</Text>
                {appt.price != null && (
                  <Text style={styles.price}>${appt.price}</Text>
                )}
              </View>

              {appt.status === "scheduled" && (
                <View style={styles.actions}>
                  <TouchableOpacity
                    style={styles.completeBtn}
                    onPress={() => completeMutation.mutate(appt.id)}
                  >
                    <Ionicons name="checkmark" size={16} color="#ffffff" />
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.noShowBtn}
                    onPress={() => noShowMutation.mutate(appt.id)}
                  >
                    <Ionicons name="close" size={16} color="#ffffff" />
                  </TouchableOpacity>
                </View>
              )}

              {appt.status === "completed" && (
                <View style={styles.donePill}>
                  <Text style={styles.doneText}>Done</Text>
                </View>
              )}
            </View>
          ))}
        </View>
      ))}
      <View style={{ height: 32 }} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  empty: { alignItems: "center", justifyContent: "center", padding: 64 },
  emptyText: { fontSize: 14, color: "#9ca3af", marginTop: 12 },
  daySection: { marginHorizontal: 16, marginTop: 20 },
  dayHeader: { fontSize: 13, fontWeight: "700", color: "#7c3aed", marginBottom: 8, textTransform: "uppercase", letterSpacing: 0.5 },
  card: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  timeCol: { width: 52, alignItems: "center", marginRight: 12 },
  timeText: { fontSize: 17, fontWeight: "700", color: "#111827" },
  ampm: { fontSize: 11, color: "#9ca3af" },
  info: { flex: 1 },
  clientName: { fontSize: 15, fontWeight: "600", color: "#111827" },
  serviceName: { fontSize: 13, color: "#6b7280", marginTop: 2 },
  price: { fontSize: 13, color: "#7c3aed", fontWeight: "600", marginTop: 2 },
  actions: { flexDirection: "row", gap: 6 },
  completeBtn: {
    backgroundColor: "#16a34a",
    borderRadius: 8,
    width: 34,
    height: 34,
    alignItems: "center",
    justifyContent: "center",
  },
  noShowBtn: {
    backgroundColor: "#dc2626",
    borderRadius: 8,
    width: 34,
    height: 34,
    alignItems: "center",
    justifyContent: "center",
  },
  donePill: {
    backgroundColor: "#dcfce7",
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
  },
  doneText: { fontSize: 12, fontWeight: "600", color: "#16a34a" },
});
