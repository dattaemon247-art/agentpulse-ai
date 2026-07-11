import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  timeout: 10000,
});

export async function fetchAgents() {
  const response = await api.get("/api/agents");
  return response.data;
}

export async function fetchAgent(agentId) {
  const response = await api.get(`/api/agents/${agentId}`);
  return response.data;
}

export async function fetchLiquidityForecast(
  agentId,
  windowMinutes = 60,
) {
  const response = await api.get(
    `/api/agents/${agentId}/liquidity-forecast`,
    {
      params: {
        window_minutes: windowMinutes,
      },
    },
  );

  return response.data;
}

export async function fetchAgentAlerts(agentId) {
  const response = await api.get("/api/alerts", {
    params: {
      agent_id: agentId,
      limit: 50,
    },
  });

  return response.data;
}

export async function generateAgentAlerts(
  agentId,
  windowMinutes = 60,
) {
  const response = await api.post(
    `/api/agents/${agentId}/generate-alerts`,
    null,
    {
      params: {
        window_minutes: windowMinutes,
      },
    },
  );

  return response.data;
}

export async function fetchCases(status = null) {
  const response = await api.get("/api/cases", {
    params: status ? { status } : {},
  });

  return response.data;
}

export async function fetchCase(caseId) {
  const response = await api.get(`/api/cases/${caseId}`);
  return response.data;
}

export async function createCaseFromAlert(
  alertId,
  payload,
) {
  const response = await api.post(
    `/api/alerts/${alertId}/cases`,
    payload,
  );

  return response.data;
}

export async function assignCase(
  caseId,
  payload,
) {
  const response = await api.patch(
    `/api/cases/${caseId}/assignment`,
    payload,
  );

  return response.data;
}

export async function updateCaseStatus(
  caseId,
  payload,
) {
  const response = await api.patch(
    `/api/cases/${caseId}/status`,
    payload,
  );

  return response.data;
}

export async function addCaseNote(
  caseId,
  payload,
) {
  const response = await api.post(
    `/api/cases/${caseId}/notes`,
    payload,
  );

  return response.data;
}

export default api;