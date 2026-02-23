import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  Alert,
} from "react-native";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Ionicons } from "@expo/vector-icons";
import { leadsApi } from "../../src/api";

const STAGE_COLORS: Record<string, { bg: string; text: string }> = {
  new: { bg: "#f3f4f6", text: "#374151" },
  contacted: { bg: "#dbeafe", text: "#1e40af" },
  qualified: { bg: "#ede9fe", text: "#5b21b6" },
  quoted: { bg: "#fef3c7", text: "#92400e" },
  follow_up: { bg: "#ffedd5", text: "#9a3412" },
  booked: { bg: "#dcfce7", text: "#166534" },
  lost: { bg: "#fee2e2", text: "#991b1b" },
};

const STAGE_LABELS: Record<string, string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  quoted: "Quoted",
  follow_up: "Follow-up",
  booked: "Booked",
  lost: "Lost",
};

export default function LeadsScreen() {
  const qc = useQueryClient();

  const { data, isLoading, refetch } = useQuery({
    queryKey: ["leads"],
    queryFn: leadsApi.list,
  });

  const qualifyMutation = useMutation({
    mutationFn: (id: number) => leadsApi.qualify(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      Alert.alert("Done", "Lead has been AI-qualified");
    },
  });

  const leads: {
    id: number;
    name: string;
    phone?: string;
    extension_type?: string;
    budget_range?: string;
    pipeline_stage: string;
    ai_qualification_score?: number;
    ai_qualification_tier?: string;
  }[] = data ?? [];

  return (
    <FlatList
      style={styles.container}
      data={leads}
      keyExtractor={(l) => String(l.id)}
      refreshing={isLoading}
      onRefresh={refetch}
      contentContainerStyle={{ padding: 16 }}
      ListEmptyComponent={
        <View style={styles.empty}>
          <Ionicons name="sparkles-outline" size={48} color="#d1d5db" />
          <Text style={styles.emptyText}>No leads yet</Text>
        </View>
      }
      renderItem={({ item: lead }) => {
        const stageStyle = STAGE_COLORS[lead.pipeline_stage] ?? STAGE_COLORS.new;
        return (
          <View style={styles.card}>
            <View style={styles.cardHeader}>
              <Text style={styles.leadName}>{lead.name}</Text>
              <View style={[styles.stagePill, { backgroundColor: stageStyle.bg }]}>
                <Text style={[styles.stageText, { color: stageStyle.text }]}>
                  {STAGE_LABELS[lead.pipeline_stage] ?? lead.pipeline_stage}
                </Text>
              </View>
            </View>

            {lead.extension_type && (
              <Text style={styles.detail}>
                <Text style={styles.detailLabel}>Type: </Text>
                {lead.extension_type}
              </Text>
            )}
            {lead.budget_range && (
              <Text style={styles.detail}>
                <Text style={styles.detailLabel}>Budget: </Text>
                {lead.budget_range}
              </Text>
            )}
            {lead.phone && (
              <Text style={styles.detail}>
                <Text style={styles.detailLabel}>Phone: </Text>
                {lead.phone}
              </Text>
            )}

            {/* Score bar */}
            {lead.ai_qualification_score != null && (
              <View style={styles.scoreRow}>
                <View style={styles.scoreBar}>
                  <View
                    style={[
                      styles.scoreBarFill,
                      { width: `${lead.ai_qualification_score}%` as unknown as number },
                    ]}
                  />
                </View>
                <Text style={styles.scoreText}>
                  {lead.ai_qualification_score}/100 · {lead.ai_qualification_tier}
                </Text>
              </View>
            )}

            {lead.ai_qualification_score == null && (
              <TouchableOpacity
                style={styles.qualifyBtn}
                onPress={() =>
                  Alert.alert(
                    "Qualify Lead",
                    `Run AI qualification for ${lead.name}?`,
                    [
                      { text: "Cancel", style: "cancel" },
                      { text: "Qualify", onPress: () => qualifyMutation.mutate(lead.id) },
                    ]
                  )
                }
              >
                <Ionicons name="sparkles" size={14} color="#7c3aed" />
                <Text style={styles.qualifyBtnText}>AI Qualify</Text>
              </TouchableOpacity>
            )}
          </View>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#f9fafb" },
  empty: { alignItems: "center", justifyContent: "center", padding: 64 },
  emptyText: { fontSize: 14, color: "#9ca3af", marginTop: 12 },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowRadius: 6,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  leadName: { fontSize: 15, fontWeight: "600", color: "#111827" },
  stagePill: { borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3 },
  stageText: { fontSize: 12, fontWeight: "600" },
  detail: { fontSize: 13, color: "#6b7280", marginBottom: 2 },
  detailLabel: { fontWeight: "600", color: "#374151" },
  scoreRow: { marginTop: 8 },
  scoreBar: {
    height: 6,
    backgroundColor: "#e5e7eb",
    borderRadius: 3,
    overflow: "hidden",
    marginBottom: 4,
  },
  scoreBarFill: { height: "100%", backgroundColor: "#7c3aed", borderRadius: 3 },
  scoreText: { fontSize: 11, color: "#6b7280" },
  qualifyBtn: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    marginTop: 8,
    alignSelf: "flex-start",
    backgroundColor: "#ede9fe",
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 8,
  },
  qualifyBtnText: { fontSize: 12, fontWeight: "600", color: "#7c3aed" },
});
