import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Sparkles,
  Send,
  MessageSquare,
  ChevronDown,
} from "lucide-react";
import { leadsApi, type Lead, type LeadCreate } from "../api/leads";
import Modal from "../components/ui/Modal";
import Spinner from "../components/ui/Spinner";

const STAGES: Lead["pipeline_stage"][] = [
  "new",
  "contacted",
  "qualified",
  "quoted",
  "follow_up",
  "booked",
  "lost",
];

const STAGE_LABELS: Record<Lead["pipeline_stage"], string> = {
  new: "New",
  contacted: "Contacted",
  qualified: "Qualified",
  quoted: "Quoted",
  follow_up: "Follow-up",
  booked: "Booked",
  lost: "Lost",
};

const STAGE_COLORS: Record<Lead["pipeline_stage"], string> = {
  new: "bg-gray-100 text-gray-700",
  contacted: "bg-blue-100 text-blue-700",
  qualified: "bg-purple-100 text-purple-700",
  quoted: "bg-yellow-100 text-yellow-700",
  follow_up: "bg-orange-100 text-orange-700",
  booked: "bg-green-100 text-green-700",
  lost: "bg-red-100 text-red-700",
};

function LeadForm({
  onSubmit,
  loading,
}: {
  onSubmit: (data: LeadCreate) => void;
  loading?: boolean;
}) {
  const [form, setForm] = useState<LeadCreate>({
    name: "",
    phone: "",
    email: "",
    source: "",
    hair_length: "",
    hair_texture: "",
    desired_length: "",
    extension_type: "",
    budget_range: "",
    timeline: "",
    notes: "",
  });
  const set = (k: keyof LeadCreate, v: string) =>
    setForm((p) => ({ ...p, [k]: v }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(form);
      }}
      className="space-y-4"
    >
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Name *</label>
          <input
            className="input"
            value={form.name}
            onChange={(e) => set("name", e.target.value)}
            required
          />
        </div>
        <div>
          <label className="label">Phone</label>
          <input
            className="input"
            value={form.phone ?? ""}
            onChange={(e) => set("phone", e.target.value)}
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Email</label>
          <input
            className="input"
            type="email"
            value={form.email ?? ""}
            onChange={(e) => set("email", e.target.value)}
          />
        </div>
        <div>
          <label className="label">Source</label>
          <input
            className="input"
            value={form.source ?? ""}
            onChange={(e) => set("source", e.target.value)}
            placeholder="Instagram, referral..."
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Current Hair Length</label>
          <input
            className="input"
            value={form.hair_length ?? ""}
            onChange={(e) => set("hair_length", e.target.value)}
          />
        </div>
        <div>
          <label className="label">Hair Texture</label>
          <input
            className="input"
            value={form.hair_texture ?? ""}
            onChange={(e) => set("hair_texture", e.target.value)}
            placeholder="fine, medium, coarse"
          />
        </div>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="label">Extension Type</label>
          <input
            className="input"
            value={form.extension_type ?? ""}
            onChange={(e) => set("extension_type", e.target.value)}
            placeholder="tape-in, weft, micro-bead..."
          />
        </div>
        <div>
          <label className="label">Budget Range</label>
          <input
            className="input"
            value={form.budget_range ?? ""}
            onChange={(e) => set("budget_range", e.target.value)}
            placeholder="$500-800"
          />
        </div>
      </div>
      <div>
        <label className="label">Notes</label>
        <textarea
          className="input min-h-[60px]"
          value={form.notes ?? ""}
          onChange={(e) => set("notes", e.target.value)}
        />
      </div>
      <div className="flex justify-end pt-2">
        <button type="submit" disabled={loading} className="btn-primary">
          {loading && <Spinner size="sm" />}
          Add Lead
        </button>
      </div>
    </form>
  );
}

function LeadCard({
  lead,
  onOpen,
}: {
  lead: Lead;
  onOpen: () => void;
}) {
  return (
    <div
      onClick={onOpen}
      className="bg-white border border-gray-200 rounded-lg p-3 cursor-pointer hover:shadow-sm transition-shadow"
    >
      <div className="font-medium text-sm text-gray-900">{lead.name}</div>
      {lead.extension_type && (
        <div className="text-xs text-gray-500 mt-0.5">{lead.extension_type}</div>
      )}
      {lead.ai_qualification_score != null && (
        <div className="mt-2 flex items-center gap-1">
          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-500 rounded-full"
              style={{ width: `${lead.ai_qualification_score}%` }}
            />
          </div>
          <span className="text-xs text-gray-500 w-8 text-right">
            {lead.ai_qualification_score}
          </span>
        </div>
      )}
      {lead.budget_range && (
        <div className="text-xs text-gray-500 mt-1">{lead.budget_range}</div>
      )}
    </div>
  );
}

function LeadDetail({
  lead,
  onClose,
}: {
  lead: Lead;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [quoteText, setQuoteText] = useState(lead.quote_text ?? "");
  const [streaming, setStreaming] = useState(false);

  const qualifyMutation = useMutation({
    mutationFn: () => leadsApi.qualify(lead.id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });

  const followUpMutation = useMutation({
    mutationFn: () => leadsApi.sendFollowUp(lead.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      alert("Follow-up SMS sent!");
    },
  });

  const sendQuoteMutation = useMutation({
    mutationFn: () => leadsApi.sendQuote(lead.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      alert("Quote sent via SMS!");
    },
  });

  const updateStageMutation = useMutation({
    mutationFn: (stage: Lead["pipeline_stage"]) =>
      leadsApi.update(lead.id, { pipeline_stage: stage }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leads"] }),
  });

  const streamQuote = async () => {
    setStreaming(true);
    setQuoteText("");
    try {
      const response = await fetch(`/api/v1/leads/${lead.id}/generate-quote`, {
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
        setQuoteText(text);
      }
    } finally {
      setStreaming(false);
    }
  };

  return (
    <Modal open onClose={onClose} title={lead.name} size="xl">
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <span className={`badge ${STAGE_COLORS[lead.pipeline_stage]}`}>
            {STAGE_LABELS[lead.pipeline_stage]}
          </span>
          <select
            className="input max-w-[160px] py-1 text-xs"
            value={lead.pipeline_stage}
            onChange={(e) =>
              updateStageMutation.mutate(
                e.target.value as Lead["pipeline_stage"]
              )
            }
          >
            {STAGES.map((s) => (
              <option key={s} value={s}>
                {STAGE_LABELS[s]}
              </option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm">
          {lead.phone && (
            <div>
              <p className="text-gray-500">Phone</p>
              <p className="font-medium">{lead.phone}</p>
            </div>
          )}
          {lead.email && (
            <div>
              <p className="text-gray-500">Email</p>
              <p className="font-medium">{lead.email}</p>
            </div>
          )}
          {lead.extension_type && (
            <div>
              <p className="text-gray-500">Extension type</p>
              <p className="font-medium">{lead.extension_type}</p>
            </div>
          )}
          {lead.budget_range && (
            <div>
              <p className="text-gray-500">Budget</p>
              <p className="font-medium">{lead.budget_range}</p>
            </div>
          )}
          {lead.hair_length && (
            <div>
              <p className="text-gray-500">Hair length</p>
              <p className="font-medium">{lead.hair_length}</p>
            </div>
          )}
          {lead.hair_texture && (
            <div>
              <p className="text-gray-500">Hair texture</p>
              <p className="font-medium">{lead.hair_texture}</p>
            </div>
          )}
        </div>

        {/* AI Qualification */}
        <div className="border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">AI Qualification</h3>
            <button
              className="btn-secondary text-xs py-1"
              onClick={() => qualifyMutation.mutate()}
              disabled={qualifyMutation.isPending}
            >
              {qualifyMutation.isPending ? (
                <Spinner size="sm" />
              ) : (
                <Sparkles className="w-3 h-3" />
              )}
              {lead.ai_qualification_score != null ? "Re-qualify" : "Qualify"}
            </button>
          </div>
          {lead.ai_qualification_score != null && (
            <div className="space-y-1">
              <div className="flex justify-between text-xs text-gray-500">
                <span>Score</span>
                <span className="font-medium text-gray-900">
                  {lead.ai_qualification_score}/100
                </span>
              </div>
              <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-brand-500 rounded-full transition-all"
                  style={{ width: `${lead.ai_qualification_score}%` }}
                />
              </div>
              {lead.ai_qualification_tier && (
                <p className="text-xs text-gray-600">
                  Tier:{" "}
                  <span className="font-medium">{lead.ai_qualification_tier}</span>
                </p>
              )}
            </div>
          )}
        </div>

        {/* Quote Builder */}
        <div className="border rounded-lg p-4 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Quote</h3>
            <div className="flex gap-2">
              <button
                className="btn-secondary text-xs py-1"
                onClick={streamQuote}
                disabled={streaming}
              >
                {streaming ? <Spinner size="sm" /> : <Sparkles className="w-3 h-3" />}
                Generate
              </button>
              <button
                className="btn-primary text-xs py-1"
                onClick={() => sendQuoteMutation.mutate()}
                disabled={!quoteText || sendQuoteMutation.isPending}
              >
                <Send className="w-3 h-3" />
                Send SMS
              </button>
            </div>
          </div>
          <textarea
            className="input min-h-[100px] text-sm"
            value={quoteText}
            onChange={(e) => setQuoteText(e.target.value)}
            placeholder="Generate or write a personalized quote..."
          />
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            className="btn-secondary flex-1"
            onClick={() => followUpMutation.mutate()}
            disabled={followUpMutation.isPending}
          >
            {followUpMutation.isPending ? (
              <Spinner size="sm" />
            ) : (
              <MessageSquare className="w-4 h-4" />
            )}
            Send Follow-up
          </button>
        </div>
      </div>
    </Modal>
  );
}

export default function ExtensionLeads() {
  const qc = useQueryClient();
  const [showAdd, setShowAdd] = useState(false);
  const [selected, setSelected] = useState<Lead | null>(null);

  const { data: leads, isLoading } = useQuery({
    queryKey: ["leads"],
    queryFn: () => leadsApi.list(),
  });

  const createMutation = useMutation({
    mutationFn: leadsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      setShowAdd(false);
    },
  });

  const byStage = STAGES.reduce<Record<string, Lead[]>>((acc, stage) => {
    acc[stage] = (leads ?? []).filter((l) => l.pipeline_stage === stage);
    return acc;
  }, {});

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowAdd(true)} className="btn-primary">
          <Plus className="w-4 h-4" />
          Add Lead
        </button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-4">
          {STAGES.filter((s) => s !== "lost").map((stage) => (
            <div key={stage} className="flex-shrink-0 w-56">
              <div className="flex items-center justify-between mb-2 px-1">
                <span className={`badge ${STAGE_COLORS[stage]}`}>
                  {STAGE_LABELS[stage]}
                </span>
                <span className="text-xs text-gray-400">
                  {byStage[stage]?.length ?? 0}
                </span>
              </div>
              <div className="space-y-2 min-h-[200px] bg-gray-50 rounded-lg p-2">
                {byStage[stage]?.map((lead) => (
                  <LeadCard
                    key={lead.id}
                    lead={lead}
                    onOpen={() => setSelected(lead)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      <Modal open={showAdd} onClose={() => setShowAdd(false)} title="Add Lead">
        <LeadForm
          onSubmit={(data) => createMutation.mutate(data)}
          loading={createMutation.isPending}
        />
      </Modal>

      {selected && (
        <LeadDetail
          lead={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
