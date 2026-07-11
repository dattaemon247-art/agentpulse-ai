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

export default api;