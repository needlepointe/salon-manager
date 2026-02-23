import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  BarChart3,
  Sparkles,
  RefreshCw,
  ChevronRight,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import ReactMarkdown from "react-markdown";
import { reportsApi } from "../api/reports";
import Spinner from "../components/ui/Spinner";
import { format } from "date-fns";

function ReportDetail({ month }: { month: string }) {
  const [aiSummary, setAiSummary] = useState("");
  const [streaming, setStreaming] = useState(false);

  const { data: report, isLoading } = useQuery({
    queryKey: ["report", month],
    queryFn: () => reportsApi.get(month),
  });

  const streamSummary = async () => {
    setStreaming(true);
    setAiSummary("");
    try {
      const response = await fetch(`/api/v1/reports/${month}/ai-summary`, {
        method: "POST",
      });
      if (!response.body) return;
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let text = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        text += decoder.decode(value, { stream: true });
        setAiSummary(text);
      }
    } finally {
      setStreaming(false);
    }
  };

  if (isLoading) return <Spinner />;
  if (!report) return <p className="text-sm text-gray-500">Report not found.</p>;

  const dailyRevenue =
    (report.charts_data_json as { daily_revenue?: { date: string; revenue: number }[] })
      ?.daily_revenue ?? [];

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Revenue", value: `$${Number(report.revenue_total ?? 0).toFixed(0)}` },
          { label: "Appointments", value: report.appointments_count ?? 0 },
          { label: "New Clients", value: report.new_clients_count ?? 0 },
          { label: "Leads Converted", value: report.leads_converted ?? 0 },
        ].map(({ label, value }) => (
          <div key={label} className="card text-center py-4">
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            <p className="text-xs text-gray-500 mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Revenue chart */}
      {dailyRevenue.length > 0 && (
        <div className="card">
          <h3 className="font-semibold text-sm mb-4">Daily Revenue</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={dailyRevenue}>
              <XAxis
                dataKey="date"
                tickFormatter={(v) => format(new Date(v), "d")}
                tick={{ fontSize: 11 }}
              />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip
                formatter={(v: number) => [`$${v.toFixed(0)}`, "Revenue"]}
                labelFormatter={(l) => format(new Date(l), "MMM d")}
              />
              <Bar dataKey="revenue" fill="#7c3aed" radius={[3, 3, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top services */}
      {report.top_services_json && (
        <div className="card">
          <h3 className="font-semibold text-sm mb-3">Top Services</h3>
          <div className="space-y-2">
            {(report.top_services_json as { service: string; count: number; revenue: number }[]).map(
              (s, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-gray-700">{s.service}</span>
                  <div className="flex gap-4 text-gray-500">
                    <span>{s.count}x</span>
                    <span>${s.revenue.toFixed(0)}</span>
                  </div>
                </div>
              )
            )}
          </div>
        </div>
      )}

      {/* AI Summary */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-brand-600" />
            AI Business Summary
          </h3>
          <button
            onClick={streamSummary}
            disabled={streaming}
            className="btn-secondary text-xs py-1"
          >
            {streaming ? <Spinner size="sm" /> : <Sparkles className="w-3 h-3" />}
            {report.ai_summary_text ? "Regenerate" : "Generate"}
          </button>
        </div>
        {streaming || aiSummary ? (
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{aiSummary || report.ai_summary_text || ""}</ReactMarkdown>
          </div>
        ) : report.ai_summary_text ? (
          <div className="prose prose-sm max-w-none text-gray-700">
            <ReactMarkdown>{report.ai_summary_text}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm text-gray-400 text-center py-6">
            Click Generate to get an AI-powered business summary
          </p>
        )}
      </div>
    </div>
  );
}

export default function Reports() {
  const qc = useQueryClient();
  const currentMonth = format(new Date(), "yyyy-MM");
  const [selectedMonth, setSelectedMonth] = useState(currentMonth);

  const { data: reportList, isLoading: listLoading } = useQuery({
    queryKey: ["reports-list"],
    queryFn: reportsApi.list,
  });

  const generateMutation = useMutation({
    mutationFn: (month: string) => reportsApi.generate(month),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reports-list"] });
      qc.invalidateQueries({ queryKey: ["report", selectedMonth] });
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-xs">
          <input
            className="input"
            type="month"
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
          />
        </div>
        <button
          onClick={() => generateMutation.mutate(selectedMonth)}
          disabled={generateMutation.isPending}
          className="btn-primary"
        >
          {generateMutation.isPending ? (
            <Spinner size="sm" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Generate Report
        </button>
      </div>

      {/* Month list sidebar + detail */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1">
          <div className="card p-0 overflow-hidden">
            <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
              <p className="text-xs font-medium text-gray-500">Past Reports</p>
            </div>
            {listLoading ? (
              <div className="flex justify-center py-8">
                <Spinner />
              </div>
            ) : !reportList || reportList.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-6">
                No reports yet
              </p>
            ) : (
              <div className="divide-y divide-gray-100">
                {(reportList as { report_month: string; revenue_total: number }[]).map((r) => (
                  <button
                    key={r.report_month}
                    onClick={() => setSelectedMonth(r.report_month)}
                    className={`w-full flex items-center justify-between px-4 py-3 text-sm hover:bg-gray-50 transition-colors ${
                      selectedMonth === r.report_month
                        ? "bg-brand-50 text-brand-700"
                        : "text-gray-700"
                    }`}
                  >
                    <span>{r.report_month}</span>
                    <ChevronRight className="w-4 h-4" />
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="lg:col-span-3">
          <ReportDetail month={selectedMonth} />
        </div>
      </div>
    </div>
  );
}
