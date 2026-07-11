import { useMemo, useState } from "react";
import {
  BriefcaseBusiness,
  CheckCircle2,
  CircleDot,
  Clock3,
  FileText,
  LoaderCircle,
  MessageSquarePlus,
  UserRoundCheck,
} from "lucide-react";

import {
  addCaseNote,
  assignCase,
  createCaseFromAlert,
  updateCaseStatus,
} from "./services/api";


const STATUS_FLOW = [
  "new",
  "acknowledged",
  "assigned",
  "investigating",
  "escalated",
  "resolved",
  "closed",
];


export default function CaseManagement({
  alerts,
  cases,
  onCasesChanged,
}) {
  const [selectedCaseId, setSelectedCaseId] =
    useState(null);

  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [ownerName, setOwnerName] =
    useState("Nusrat Jahan");

  const [ownerRole, setOwnerRole] =
    useState("Field Operations Officer");

  const [priority, setPriority] =
    useState("high");

  const [note, setNote] =
    useState("");

  const [resolutionSummary, setResolutionSummary] =
    useState("");

  const selectedCase = useMemo(
    () =>
      cases.find(
        (item) => item.id === selectedCaseId,
      ) ?? cases[0] ?? null,
    [cases, selectedCaseId],
  );

  const linkedAlertIds = new Set(
    cases.map((item) => item.alert_id),
  );

  const alertsWithoutCases = alerts.filter(
    (alert) => !linkedAlertIds.has(alert.id),
  );


  async function runAction(action, successMessage) {
    try {
      setBusy(true);
      setError("");
      setMessage("");

      await action();
      await onCasesChanged();

      setMessage(successMessage);
    } catch (requestError) {
      console.error(requestError);

      setError(
        requestError?.response?.data?.detail ??
          "Case operation failed.",
      );
    } finally {
      setBusy(false);
    }
  }


  async function handleCreateCase(alertId) {
    await runAction(
      () =>
        createCaseFromAlert(alertId, {
          owner_name: ownerName || null,
          owner_role: ownerRole || null,
          priority,
        }),
      "Case created successfully.",
    );
  }


  async function handleAssignCase() {
    if (!selectedCase) {
      return;
    }

    await runAction(
      () =>
        assignCase(selectedCase.id, {
          owner_name: ownerName,
          owner_role: ownerRole,
          actor: "Operations Coordinator",
        }),
      "Case assignment updated.",
    );
  }


  async function handleStatusUpdate(status) {
    if (!selectedCase) {
      return;
    }

    const payload = {
      status,
      actor: ownerName || "Operations User",
      note:
        note.trim() ||
        `Case moved to ${status}.`,
      resolution_summary:
        status === "resolved"
          ? resolutionSummary.trim()
          : null,
    };

    await runAction(
      () =>
        updateCaseStatus(
          selectedCase.id,
          payload,
        ),
      `Case moved to ${status}.`,
    );

    setNote("");

    if (status === "resolved") {
      setResolutionSummary("");
    }
  }


  async function handleAddNote() {
    if (!selectedCase || !note.trim()) {
      return;
    }

    await runAction(
      () =>
        addCaseNote(selectedCase.id, {
          message: note.trim(),
          actor:
            ownerName || "Operations User",
        }),
      "Case note added.",
    );

    setNote("");
  }


  return (
    <section className="mt-8 pb-12">
      <div>
        <h3 className="text-xl font-bold">
          Case management
        </h3>

        <p className="mt-1 text-sm text-slate-500">
          Coordinate ownership, investigation,
          escalation, resolution, and closure.
        </p>
      </div>

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700">
          {message}
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      <div className="mt-5 grid gap-5 xl:grid-cols-[0.9fr_1.4fr]">
        <div className="space-y-5">
          <CreateCasePanel
            alerts={alertsWithoutCases}
            ownerName={ownerName}
            setOwnerName={setOwnerName}
            ownerRole={ownerRole}
            setOwnerRole={setOwnerRole}
            priority={priority}
            setPriority={setPriority}
            busy={busy}
            onCreateCase={handleCreateCase}
          />

          <CaseList
            cases={cases}
            selectedCaseId={
              selectedCase?.id ?? null
            }
            onSelect={setSelectedCaseId}
          />
        </div>

        <CaseDetails
          caseData={selectedCase}
          ownerName={ownerName}
          setOwnerName={setOwnerName}
          ownerRole={ownerRole}
          setOwnerRole={setOwnerRole}
          note={note}
          setNote={setNote}
          resolutionSummary={resolutionSummary}
          setResolutionSummary={
            setResolutionSummary
          }
          busy={busy}
          onAssign={handleAssignCase}
          onAddNote={handleAddNote}
          onStatusUpdate={handleStatusUpdate}
        />
      </div>
    </section>
  );
}


function CreateCasePanel({
  alerts,
  ownerName,
  setOwnerName,
  ownerRole,
  setOwnerRole,
  priority,
  setPriority,
  busy,
  onCreateCase,
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
          <BriefcaseBusiness size={20} />
        </div>

        <div>
          <h4 className="font-bold">
            Create case from alert
          </h4>

          <p className="text-xs text-slate-500">
            {alerts.length} alert(s) without a case
          </p>
        </div>
      </div>

      <div className="mt-4 grid gap-3">
        <input
          value={ownerName}
          onChange={(event) =>
            setOwnerName(event.target.value)
          }
          placeholder="Owner name"
          className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
        />

        <input
          value={ownerRole}
          onChange={(event) =>
            setOwnerRole(event.target.value)
          }
          placeholder="Owner role"
          className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
        />

        <select
          value={priority}
          onChange={(event) =>
            setPriority(event.target.value)
          }
          className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm outline-none focus:border-indigo-500"
        >
          <option value="low">Low priority</option>
          <option value="medium">
            Medium priority
          </option>
          <option value="high">
            High priority
          </option>
          <option value="critical">
            Critical priority
          </option>
        </select>
      </div>

      <div className="mt-4 space-y-3">
        {alerts.length === 0 ? (
          <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
            All current alerts already have cases.
          </p>
        ) : (
          alerts.map((alert) => (
            <div
              key={alert.id}
              className="rounded-xl border border-slate-200 p-3"
            >
              <p className="text-xs font-semibold uppercase text-slate-400">
                Alert #{alert.id}
              </p>

              <p className="mt-1 text-sm font-bold">
                {alert.title}
              </p>

              <p className="mt-1 text-xs text-slate-500">
                {alert.provider_name ??
                  "Shared cash"}{" "}
                · {alert.severity}
              </p>

              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  onCreateCase(alert.id)
                }
                className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-60"
              >
                {busy && (
                  <LoaderCircle
                    size={16}
                    className="animate-spin"
                  />
                )}

                Create operational case
              </button>
            </div>
          ))
        )}
      </div>
    </article>
  );
}


function CaseList({
  cases,
  selectedCaseId,
  onSelect,
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h4 className="font-bold">
        Cases
      </h4>

      <div className="mt-4 space-y-3">
        {cases.length === 0 ? (
          <p className="rounded-xl bg-slate-50 p-4 text-sm text-slate-500">
            No cases created yet.
          </p>
        ) : (
          cases.map((caseItem) => (
            <button
              key={caseItem.id}
              type="button"
              onClick={() =>
                onSelect(caseItem.id)
              }
              className={`w-full rounded-xl border p-4 text-left transition ${
                selectedCaseId === caseItem.id
                  ? "border-indigo-400 bg-indigo-50"
                  : "border-slate-200 bg-white hover:bg-slate-50"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold">
                  {caseItem.case_code}
                </span>

                <StatusBadge
                  status={caseItem.status}
                />
              </div>

              <p className="mt-2 text-xs text-slate-500">
                Alert #{caseItem.alert_id}
              </p>

              <p className="mt-1 text-sm text-slate-600">
                {caseItem.owner_name ??
                  "Unassigned"}
              </p>
            </button>
          ))
        )}
      </div>
    </article>
  );
}


function CaseDetails({
  caseData,
  ownerName,
  setOwnerName,
  ownerRole,
  setOwnerRole,
  note,
  setNote,
  resolutionSummary,
  setResolutionSummary,
  busy,
  onAssign,
  onAddNote,
  onStatusUpdate,
}) {
  if (!caseData) {
    return (
      <article className="rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
        <BriefcaseBusiness
          size={38}
          className="mx-auto text-slate-300"
        />

        <p className="mt-3 font-bold">
          Select or create a case
        </p>
      </article>
    );
  }

  const nextStatuses =
    getNextStatuses(caseData.status);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-indigo-600">
            Operational Case
          </p>

          <h4 className="mt-1 text-xl font-bold">
            {caseData.case_code}
          </h4>

          <p className="mt-1 text-sm text-slate-500">
            Linked alert #{caseData.alert_id}
          </p>
        </div>

        <StatusBadge status={caseData.status} />
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-3">
        <InfoCard
          label="Owner"
          value={
            caseData.owner_name ?? "Unassigned"
          }
        />

        <InfoCard
          label="Role"
          value={
            caseData.owner_role ??
            "Not specified"
          }
        />

        <InfoCard
          label="Priority"
          value={caseData.priority}
        />
      </div>

      <div className="mt-6 rounded-xl border border-slate-200 p-4">
        <div className="flex items-center gap-2">
          <UserRoundCheck size={18} />
          <h5 className="font-bold">
            Assignment
          </h5>
        </div>

        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <input
            value={ownerName}
            onChange={(event) =>
              setOwnerName(event.target.value)
            }
            placeholder="Owner name"
            className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          />

          <input
            value={ownerRole}
            onChange={(event) =>
              setOwnerRole(event.target.value)
            }
            placeholder="Owner role"
            className="rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          />
        </div>

        <button
          type="button"
          onClick={onAssign}
          disabled={
            busy ||
            !ownerName.trim() ||
            !ownerRole.trim()
          }
          className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          Update assignment
        </button>
      </div>

      <div className="mt-5 rounded-xl border border-slate-200 p-4">
        <h5 className="font-bold">
          Status workflow
        </h5>

        <div className="mt-3 flex flex-wrap gap-2">
          {STATUS_FLOW.map((status) => (
            <div
              key={status}
              className={`rounded-full px-3 py-1.5 text-xs font-semibold ${
                status === caseData.status
                  ? "bg-indigo-600 text-white"
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              {status}
            </div>
          ))}
        </div>

        <textarea
          value={note}
          onChange={(event) =>
            setNote(event.target.value)
          }
          placeholder="Status note or case note"
          rows={3}
          className="mt-4 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
        />

        {nextStatuses.includes("resolved") && (
          <textarea
            value={resolutionSummary}
            onChange={(event) =>
              setResolutionSummary(
                event.target.value,
              )
            }
            placeholder="Resolution summary required for resolved status"
            rows={3}
            className="mt-3 w-full rounded-xl border border-slate-300 px-3 py-2.5 text-sm"
          />
        )}

        <div className="mt-3 flex flex-wrap gap-2">
          {nextStatuses.map((status) => (
            <button
              key={status}
              type="button"
              disabled={
                busy ||
                (status === "resolved" &&
                  !resolutionSummary.trim())
              }
              onClick={() =>
                onStatusUpdate(status)
              }
              className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              Move to {status}
            </button>
          ))}

          <button
            type="button"
            disabled={
              busy || !note.trim()
            }
            onClick={onAddNote}
            className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:opacity-50"
          >
            <MessageSquarePlus size={16} />
            Add note
          </button>
        </div>
      </div>

      {caseData.resolution_summary && (
        <div className="mt-5 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-center gap-2 font-bold text-emerald-800">
            <CheckCircle2 size={18} />
            Resolution summary
          </div>

          <p className="mt-2 text-sm leading-6 text-emerald-800">
            {caseData.resolution_summary}
          </p>
        </div>
      )}

      <div className="mt-6">
        <div className="flex items-center gap-2">
          <Clock3 size={18} />
          <h5 className="font-bold">
            Audit timeline
          </h5>
        </div>

        <div className="mt-4 space-y-4">
          {caseData.events.map((event) => (
            <div
              key={event.id}
              className="relative border-l-2 border-slate-200 pl-5"
            >
              <CircleDot
                size={16}
                className="absolute -left-[9px] top-0 bg-white text-indigo-600"
              />

              <div className="flex flex-wrap items-center gap-2">
                <span className="text-sm font-bold">
                  {event.event_type}
                </span>

                <span className="text-xs text-slate-400">
                  {formatDateTime(
                    event.created_at,
                  )}
                </span>
              </div>

              <p className="mt-1 text-sm leading-6 text-slate-600">
                {event.message}
              </p>

              <p className="mt-1 text-xs text-slate-400">
                Actor: {event.actor}
              </p>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}


function InfoCard({ label, value }) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-sm font-bold capitalize">
        {value}
      </p>
    </div>
  );
}


function StatusBadge({ status }) {
  const styles = {
    new: "bg-slate-100 text-slate-700",
    acknowledged:
      "bg-sky-100 text-sky-700",
    assigned:
      "bg-indigo-100 text-indigo-700",
    investigating:
      "bg-amber-100 text-amber-700",
    escalated:
      "bg-red-100 text-red-700",
    resolved:
      "bg-emerald-100 text-emerald-700",
    closed:
      "bg-slate-800 text-white",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase ${
        styles[status] ??
        "bg-slate-100 text-slate-600"
      }`}
    >
      {status}
    </span>
  );
}


function getNextStatuses(currentStatus) {
  const transitions = {
    new: ["acknowledged", "assigned"],
    acknowledged: [
      "assigned",
      "investigating",
    ],
    assigned: [
      "acknowledged",
      "investigating",
      "escalated",
    ],
    investigating: [
      "escalated",
      "resolved",
    ],
    escalated: [
      "investigating",
      "resolved",
    ],
    resolved: ["closed", "investigating"],
    closed: [],
  };

  return transitions[currentStatus] ?? [];
}


function formatDateTime(value) {
  return new Date(value).toLocaleString(
    "en-BD",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  );
}