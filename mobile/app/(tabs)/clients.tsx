import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  TextInput,
  StyleSheet,
  Alert,
} from "react-native";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { clientsApi } from "../../src/api";

export default function ClientsScreen() {
  const qc = useQueryClient();
  const [search, setSearch] = useState("");

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["clients", search],
    queryFn: () => clientsApi.list(search),
  });

  const outreachMutation = useMutation({
    mutationFn: (id: number) => clientsApi.sendOutreach(id),
    onSuccess: () => Alert.alert("Sent", "Re-engagement SMS sent!"),
    onError: () => Alert.alert("Error", "Failed to send SMS"),
  });

  const clients: {
    id: number;
    full_name: string;
    phone: string;
    email?: string;
    total_visits: number;
    total_spent: number;
    last_visit_date?: string;
    is_lapsed: boolean;
  }[] = data ?? [];

  return (
    <View style={styles.container}>
      <View style={styles.searchBar}>
        <Ionicons name="search" size={16} color="#9ca3af" style={{ marginRight: 8 }} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search clients..."
          placeholderTextColor="#9ca3af"
          value={search}
          onChangeText={setSearch}
        />
        {search.length > 0 && (
          <TouchableOpacity onPress={() => setSearch("")}>
            <Ionicons name="close-circle" size={16} color="#9ca3af" />
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        data={clients}
        keyExtractor={(c) => String(c.id)}
        refreshing={isLoading}
        onRefresh={refetch}
        contentContainerStyle={{ padding: 16, paddingTop: 8 }}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Ionicons name="people-outline" size={48} color="#d1d5db" />
            <Text style={styles.emptyText}>No clients found</Text>
          </View>
        }
        renderItem={({ item: client }) => (
          <View style={styles.card}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {client.full_name.charAt(0).toUpperCase()}
              </Text>
            </View>

            <View style={styles.info}>
              <View style={styles.nameRow}>
                <Text style={styles.name}>{client.full_name}</Text>
                {client.is_lapsed && (
                  <View style={styles.lapsedBadge}>
                    <Text style={styles.lapsedText}>Lapsed</Text>
                  </View>
                )}
              </View>
              <Text style={styles.phone}>{client.phone}</Text>
              <Text style={styles.meta}>
                {client.total_visits} visits · ${Number(client.total_spent).toFixed(0)} total
              </Text>
            </View>

            {client.is_lapsed && (
              <TouchableOpacity
                style={styles.reengageBtn}
                onPress={() =>
                  Alert.alert(
                    "Send Re-engagement",
                    `Send AI-drafted SMS to ${client.full_name}?`,
                    [
                      { text: "Cancel", style: "cancel" },
                      { text: "Send", onPress: () => outreachMutation.mutate(client.id) },
                    ]
                  )
                }
              >
                <Ionicons name="refresh" size={16} color="#7c3aed" />
              </TouchableOpacity>
            )}
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  searchBar: {
    flexDirection: "row",
    alignItems: "center",
    backgroundColor: "#ffffff",
    margin: 16,
    marginBottom: 0,
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: "#e5e7eb",
  },
  searchInput: { flex: 1, fontSize: 15, color: "#111827" },
  empty: { alignItems: "center", justifyContent: "center", padding: 64 },
  emptyText: { fontSize: 14, color: "#9ca3af", marginTop: 12 },
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
  avatar: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#ede9fe",
    alignItems: "center",
    justifyContent: "center",
    marginRight: 12,
  },
  avatarText: { fontSize: 18, fontWeight: "700", color: "#7c3aed" },
  info: { flex: 1 },
  nameRow: { flexDirection: "row", alignItems: "center", gap: 6 },
  name: { fontSize: 15, fontWeight: "600", color: "#111827" },
  lapsedBadge: {
    backgroundColor: "#fef3c7",
    borderRadius: 6,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  lapsedText: { fontSize: 11, color: "#d97706", fontWeight: "600" },
  phone: { fontSize: 13, color: "#6b7280", marginTop: 2 },
  meta: { fontSize: 12, color: "#9ca3af", marginTop: 2 },
  reengageBtn: {
    width: 38,
    height: 38,
    borderRadius: 10,
    backgroundColor: "#ede9fe",
    alignItems: "center",
    justifyContent: "center",
  },
});
