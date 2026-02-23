import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Heart, Send, Clock } from "lucide-react";
import { aftercareApi } from "../api/aftercare";
import Spinner from "../components/ui/Spinner";
import EmptyState from "../components/ui/EmptyState";
import { format } from "date-fns";

interface PendingSeq {
  id: number;
  type: "d3" | "w2";
  client_name: string;
  service_type: string;
  appointment_date: string;
}

interface Sequence {
  id: number;
  client_name: string;
  service_type: string;
  appointment_date: string;
  d3_sent_at?: string;
  d3_response?: string;
  w2_sent_at?: string;
  w2_response?: string;
  upsell_offer_sent: boolean;
  upsell_converted: boolean;
}

export default function Aftercare() {
  const qc = useQueryClient();

  const { data: pending, isLoading: pendingLoading } = useQuery({
    queryKey: ["aftercare-pending"],
    queryFn: aftercareApi.getPending,
    refetchInterval: 60_000,
  });

  const { data: all, isLoading: allLoading } = useQuery({
    queryKey: ["aftercare-all"],
    queryFn: aftercareApi.list,
  });

  const d3Mutation = useMutation({
    mutationFn: (id: number) => aftercareApi.sendD3(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aftercare-pending"] });
      qc.invalidateQueries({ queryKey: ["aftercare-all"] });
    },
  });

  const w2Mutation = useMutation({
    mutationFn: (id: number) => aftercareApi.sendW2(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["aftercare-pending"] });
      qc.invalidateQueries({ queryKey: ["aftercare-all"] });
    },
  });

  const pendingItems: PendingSeq[] = pending ?? [];
  const sequences: Sequence[] = all ?? [];

  return (
    <div className="space-y-6">
      {/* Pending */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Clock className="w-5 h-5 text-yellow-500" />
          <h2 className="font-semibold">Due Now</h2>
          {pendingItems.length > 0 && (
            <span className="badge badge-yellow">{pendingItems.length}</span>
          )}
        </div>

        {pendingLoading ? (
          <div className="flex justify-center py-8">
            <Spinner />
          </div>
        ) : pendingItems.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            No aftercare messages due right now
          </p>
        ) : (
          <div className="space-y-3">
            {pendingItems.map((item) => (
              <div
                key={`${item.id}-${item.type}`}
                className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-100 rounded-lg"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {item.client_name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {item.service_type} —{" "}
                    {format(new Date(item.appointment_date), "MMM d")}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`badge ${
                      item.type === "d3" ? "badge-blue" : "badge-purple"
                    }`}
                  >
                    {item.type === "d3" ? "Day 3" : "Week 2"}
                  </span>
                  <button
                    className="btn-primary text-xs py-1"
                    disabled={
                      item.type === "d3"
                        ? d3Mutation.isPending
                        : w2Mutation.isPending
                    }
                    onClick={() =>
                      item.type === "d3"
                        ? d3Mutation.mutate(item.id)
                        : w2Mutation.mutate(item.id)
                    }
                  >
                    <Send className="w-3 h-3" />
                    Send
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All sequences */}
      <div className="card p-0 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center gap-2">
          <Heart className="w-5 h-5 text-brand-600" />
          <h2 className="font-semibold">All Sequences</h2>
        </div>

        {allLoading ? (
          <div className="flex justify-center py-16">
            <Spinner />
          </div>
        ) : sequences.length === 0 ? (
          <EmptyState
            icon={<Heart className="w-12 h-12" />}
            title="No aftercare sequences yet"
            description="Complete appointments to automatically create aftercare sequences"
          />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Client
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Service
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Day 3
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Week 2
                </th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">
                  Upsell
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sequences.map((seq) => (
                <tr key={seq.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{seq.client_name}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {seq.service_type}
                  </td>
                  <td className="px-4 py-3">
                    {seq.d3_sent_at ? (
                      <div>
                        <span className="badge badge-green">Sent</span>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {format(new Date(seq.d3_sent_at), "MMM d")}
                        </p>
                        {seq.d3_response && (
                          <p className="text-xs text-gray-700 italic mt-0.5 truncate max-w-[150px]">
                            "{seq.d3_response}"
                          </p>
                        )}
                      </div>
                    ) : (
                      <span className="badge badge-gray">Pending</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {seq.w2_sent_at ? (
                      <div>
                        <span className="badge badge-green">Sent</span>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {format(new Date(seq.w2_sent_at), "MMM d")}
                        </p>
                      </div>
                    ) : seq.d3_sent_at ? (
                      <span className="badge badge-yellow">Due soon</span>
                    ) : (
                      <span className="badge badge-gray">Waiting</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {seq.upsell_converted ? (
                      <span className="badge badge-green">Converted</span>
                    ) : seq.upsell_offer_sent ? (
                      <span className="badge badge-blue">Sent</span>
                    ) : (
                      <span className="badge badge-gray">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
