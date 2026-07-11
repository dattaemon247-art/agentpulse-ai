import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  Banknote,
  ChevronRight,
  Clock3,
  Database,
  LoaderCircle,
  MapPin,
  RefreshCw,
  ShieldCheck,
  WalletCards,
} from "lucide-react";

import {
  fetchAgent,
  fetchAgentAlerts,
  fetchAgents,
  fetchLiquidityForecast,
  generateAgentAlerts,
} from "./services/api";


function App() {
  const [agents, setAgents] = useState([]);
  const [selectedAgentId, setSelectedAgentId] = useState(null);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [forecasts, setForecasts] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const [loading, setLoading] = useState(true);
  const [generatingAlerts, setGeneratingAlerts] = useState(false);
  const [error, setError] = useState("");
  const [notification, setNotification] = useState("");


  useEffect(() => {
    loadInitialData();
  }, []);


  useEffect(() => {
    if (!selectedAgentId) {
      return;
    }

    loadSelectedAgentData(selectedAgentId);
  }, [selectedAgentId]);


  async function loadInitialData() {
    try {
      setLoading(true);
      setError("");

      const agentList = await fetchAgents();

      setAgents(agentList);

      if (agentList.length > 0) {
        setSelectedAgentId(agentList[0].id);
      }
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Backend থেকে agent data load করা যায়নি। Backend server চলছে কি না দেখুন।",
      );
    } finally {
      setLoading(false);
    }
  }


  async function loadSelectedAgentData(agentId) {
    try {
      setLoading(true);
      setError("");

      const [
        agentData,
        forecastData,
        alertData,
      ] = await Promise.all([
        fetchAgent(agentId),
        fetchLiquidityForecast(agentId, 60),
        fetchAgentAlerts(agentId),
      ]);

      setSelectedAgent(agentData);
      setForecasts(forecastData);
      setAlerts(alertData);
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Selected agent-এর dashboard data load করা যায়নি।",
      );
    } finally {
      setLoading(false);
    }
  }


  async function handleGenerateAlerts() {
    if (!selectedAgentId) {
      return;
    }

    try {
      setGeneratingAlerts(true);
      setError("");
      setNotification("");

      const result = await generateAgentAlerts(
        selectedAgentId,
        60,
      );

      setNotification(
        `${result.created_count}টি নতুন alert তৈরি হয়েছে এবং ${result.skipped_duplicate_count}টি duplicate alert skip হয়েছে।`,
      );

      const refreshedAlerts = await fetchAgentAlerts(
        selectedAgentId,
      );

      setAlerts(refreshedAlerts);
    } catch (requestError) {
      console.error(requestError);

      setError(
        "Alert generate করা যায়নি। Backend log check করুন।",
      );
    } finally {
      setGeneratingAlerts(false);
    }
  }


  const criticalForecasts = useMemo(
    () =>
      forecasts.filter((forecast) =>
        ["critical", "high"].includes(
          forecast.severity,
        ),
      ),
    [forecasts],
  );


  const totalProviderBalance = useMemo(
    () =>
      selectedAgent?.balances?.reduce(
        (total, balance) => total + balance.balance,
        0,
      ) ?? 0,
    [selectedAgent],
  );


  if (loading && !selectedAgent) {
    return <FullPageLoader />;
  }


  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
        <section className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-indigo-600">
              Operations Command Center
            </p>

            <h2 className="mt-2 text-3xl font-bold tracking-tight">
              Multi-provider liquidity intelligence
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Monitor provider balances, predict liquidity pressure,
              detect unusual activity, and support safe human decisions.
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <select
              value={selectedAgentId ?? ""}
              onChange={(event) =>
                setSelectedAgentId(
                  Number(event.target.value),
                )
              }
              className="rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-medium outline-none focus:border-indigo-500"
            >
              {agents.map((agent) => (
                <option
                  key={agent.id}
                  value={agent.id}
                >
                  {agent.agent_code} — {agent.name}
                </option>
              ))}
            </select>

            <button
              type="button"
              onClick={handleGenerateAlerts}
              disabled={generatingAlerts}
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {generatingAlerts ? (
                <LoaderCircle
                  size={18}
                  className="animate-spin"
                />
              ) : (
                <RefreshCw size={18} />
              )}

              Generate Alerts
            </button>
          </div>
        </section>

        {error && (
          <MessageBanner
            type="error"
            message={error}
          />
        )}

        {notification && (
          <MessageBanner
            type="success"
            message={notification}
          />
        )}

        {selectedAgent && (
          <>
            <AgentSummary agent={selectedAgent} />

            <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard
                icon={<Banknote size={22} />}
                label="Physical cash"
                value={formatCurrency(
                  selectedAgent.physical_cash,
                )}
                helper="Shared across all providers"
              />

              <MetricCard
                icon={<WalletCards size={22} />}
                label="Provider balances"
                value={formatCurrency(
                  totalProviderBalance,
                )}
                helper="Balances remain logically separated"
              />

              <MetricCard
                icon={<AlertTriangle size={22} />}
                label="Open alerts"
                value={alerts.filter(
                  (alert) =>
                    !["resolved", "closed"].includes(
                      alert.status,
                    ),
                ).length}
                helper="Human review may be required"
              />

              <MetricCard
                icon={<Activity size={22} />}
                label="High-risk forecasts"
                value={criticalForecasts.length}
                helper="Critical or high severity"
              />
            </section>

            <ProviderBalances
              balances={selectedAgent.balances}
            />

            <ForecastSection forecasts={forecasts} />

            <AlertsSection alerts={alerts} />
          </>
        )}
      </main>
    </div>
  );
}


function Header() {
  return (
    <header className="border-b border-slate-200 bg-slate-950 text-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-500">
            <Activity size={24} />
          </div>

          <div>
            <h1 className="text-lg font-bold">
              AgentPulse AI
            </h1>

            <p className="text-xs text-slate-400">
              Liquidity & Risk Intelligence Platform
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1.5 text-xs font-semibold text-emerald-300">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          Synthetic demo environment
        </div>
      </div>
    </header>
  );
}


function AgentSummary({ agent }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-xl font-bold">
              {agent.name}
            </h3>

            <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase text-emerald-700">
              {agent.status}
            </span>
          </div>

          <div className="mt-2 flex flex-wrap gap-4 text-sm text-slate-500">
            <span className="font-medium">
              {agent.agent_code}
            </span>

            <span className="flex items-center gap-1.5">
              <MapPin size={15} />
              {agent.area}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2 rounded-xl bg-indigo-50 px-4 py-3 text-sm font-medium text-indigo-700">
          <ShieldCheck size={18} />
          Advisory system — human decision required
        </div>
      </div>
    </section>
  );
}


function MetricCard({
  icon,
  label,
  value,
  helper,
}) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600">
          {icon}
        </div>

        <ChevronRight
          size={18}
          className="text-slate-300"
        />
      </div>

      <p className="mt-5 text-sm font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-1 text-2xl font-bold">
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {helper}
      </p>
    </article>
  );
}


function ProviderBalances({ balances }) {
  return (
    <section className="mt-6">
      <SectionHeading
        title="Provider balances"
        subtitle="Each provider balance is monitored separately."
      />

      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {balances.map((balance) => (
          <article
            key={balance.id}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  {balance.provider.name}
                </p>

                <p className="mt-2 text-2xl font-bold">
                  {formatCurrency(balance.balance)}
                </p>
              </div>

              <DataStatusBadge
                status={balance.data_status}
              />
            </div>

            <div className="mt-5 flex items-center gap-2 text-xs text-slate-500">
              <Database size={14} />

              Last update:{" "}
              {formatDateTime(balance.last_updated)}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}


function ForecastSection({ forecasts }) {
  return (
    <section className="mt-8">
      <SectionHeading
        title="Liquidity forecast"
        subtitle="Forecast based on recent transaction demand."
      />

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {forecasts.map((forecast) => (
          <article
            key={forecast.provider_id}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-slate-500">
                  {forecast.provider_name}
                </p>

                <h4 className="mt-1 text-lg font-bold">
                  {formatRiskType(
                    forecast.risk_type,
                  )}
                </h4>
              </div>

              <SeverityBadge
                severity={forecast.severity}
              />
            </div>

            <div className="mt-5 rounded-xl bg-slate-50 p-4">
              <div className="flex items-center gap-2 text-sm text-slate-500">
                <Clock3 size={17} />
                Estimated shortage
              </div>

              <p className="mt-2 text-2xl font-bold">
                {forecast.estimated_shortage_minutes
                  ? `${forecast.estimated_shortage_minutes} min`
                  : "No immediate risk"}
              </p>
            </div>

            <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
              <SmallStat
                label="Confidence"
                value={`${Math.round(
                  forecast.confidence * 100,
                )}%`}
              />

              <SmallStat
                label="Transactions"
                value={forecast.transaction_count}
              />

              <SmallStat
                label="Cash-in"
                value={formatCurrency(
                  forecast.cash_in_total,
                )}
              />

              <SmallStat
                label="Cash-out"
                value={formatCurrency(
                  forecast.cash_out_total,
                )}
              />
            </div>

            <p className="mt-4 text-sm leading-6 text-slate-600">
              {forecast.explanation}
            </p>

            <div className="mt-4 rounded-xl border border-indigo-100 bg-indigo-50 p-3 text-sm leading-6 text-indigo-800">
              <strong>Recommended:</strong>{" "}
              {forecast.recommended_action}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}


function AlertsSection({ alerts }) {
  return (
    <section className="mt-8 pb-10">
      <SectionHeading
        title="Saved alerts"
        subtitle="Explainable alerts stored for operational review."
      />

      <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        {alerts.length === 0 ? (
          <div className="p-8 text-center">
            <ShieldCheck
              size={36}
              className="mx-auto text-slate-300"
            />

            <p className="mt-3 font-semibold">
              No saved alerts
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Click Generate Alerts to analyse the
              selected agent.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {alerts.map((alert) => (
              <article
                key={alert.id}
                className="p-5"
              >
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <SeverityBadge
                        severity={alert.severity}
                      />

                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold uppercase text-slate-600">
                        {alert.status}
                      </span>

                      <span className="text-xs text-slate-400">
                        {alert.provider_name ??
                          "Shared cash"}
                      </span>
                    </div>

                    <h4 className="mt-3 font-bold">
                      {alert.title}
                    </h4>

                    <p className="mt-2 text-sm leading-6 text-slate-600">
                      {alert.reason}
                    </p>
                  </div>

                  <div className="min-w-28 rounded-xl bg-slate-50 px-4 py-3 text-center">
                    <p className="text-xs font-medium uppercase text-slate-500">
                      Confidence
                    </p>

                    <p className="mt-1 text-xl font-bold">
                      {Math.round(
                        alert.confidence * 100,
                      )}
                      %
                    </p>
                  </div>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-2">
                  <div className="rounded-xl bg-amber-50 p-3 text-sm leading-6 text-amber-900">
                    <strong>
                      Possible explanation:
                    </strong>{" "}
                    {alert.possible_explanation}
                  </div>

                  <div className="rounded-xl bg-indigo-50 p-3 text-sm leading-6 text-indigo-900">
                    <strong>
                      Recommended action:
                    </strong>{" "}
                    {alert.recommended_action}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}


function SectionHeading({
  title,
  subtitle,
}) {
  return (
    <div>
      <h3 className="text-xl font-bold">
        {title}
      </h3>

      <p className="mt-1 text-sm text-slate-500">
        {subtitle}
      </p>
    </div>
  );
}


function SmallStat({
  label,
  value,
}) {
  return (
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs font-medium text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-bold">
        {value}
      </p>
    </div>
  );
}


function DataStatusBadge({ status }) {
  const styles = {
    live: "bg-emerald-100 text-emerald-700",
    delayed: "bg-amber-100 text-amber-700",
    missing: "bg-red-100 text-red-700",
    conflicting: "bg-purple-100 text-purple-700",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-semibold uppercase ${
        styles[status] ??
        "bg-slate-100 text-slate-600"
      }`}
    >
      {status}
    </span>
  );
}


function SeverityBadge({ severity }) {
  const styles = {
    critical: "bg-red-100 text-red-700",
    high: "bg-orange-100 text-orange-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-emerald-100 text-emerald-700",
  };

  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-bold uppercase ${
        styles[severity] ??
        "bg-slate-100 text-slate-600"
      }`}
    >
      {severity}
    </span>
  );
}


function MessageBanner({
  type,
  message,
}) {
  const style =
    type === "error"
      ? "border-red-200 bg-red-50 text-red-700"
      : "border-emerald-200 bg-emerald-50 text-emerald-700";

  return (
    <div
      className={`mb-5 rounded-xl border px-4 py-3 text-sm font-medium ${style}`}
    >
      {message}
    </div>
  );
}


function FullPageLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-100">
      <div className="text-center">
        <LoaderCircle
          size={38}
          className="mx-auto animate-spin text-indigo-600"
        />

        <p className="mt-3 text-sm font-medium text-slate-600">
          Loading AgentPulse dashboard...
        </p>
      </div>
    </div>
  );
}


function formatCurrency(value) {
  return new Intl.NumberFormat("en-BD", {
    style: "currency",
    currency: "BDT",
    maximumFractionDigits: 0,
  }).format(value ?? 0);
}


function formatDateTime(value) {
  if (!value) {
    return "Unknown";
  }

  return new Date(value).toLocaleString("en-BD", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}


function formatRiskType(riskType) {
  const labels = {
    provider_float: "Provider float pressure",
    physical_cash: "Physical cash pressure",
    stable: "Stable liquidity",
  };

  return labels[riskType] ?? riskType;
}


export default App;