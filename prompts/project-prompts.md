# AgentPulse AI — Prompt Log

## 1. Project Planning
- Prompt: Build a multi-provider MFS liquidity and risk intelligence platform.
- Goal: Define architecture, users, and problem statement.

## 2. Backend Setup
- Prompt: Create FastAPI backend with Agent, Provider, Balance, Transaction, Alert, Case, and CaseEvent models.
- Goal: Build the main backend structure.

## 3. Synthetic Data
- Prompt: Generate seven days of synthetic transactions for bKash, Nagad, and Rocket.
- Goal: Create realistic test data without using real customer data.

## 4. Liquidity Forecasting
- Prompt: Calculate provider float and physical cash pressure using recent transaction rates.
- Prompt: Compare current demand with a seven-day same-hour baseline.
- Prompt: Use 75% recent activity and 25% historical baseline.
- Goal: Predict shortage time, severity, and confidence.

## 5. Anomaly Detection
- Prompt: Detect repeated amounts, high-value bursts, and transaction velocity spikes.
- Goal: Identify unusual activity without declaring fraud.

## 6. Alert Engine
- Prompt: Generate explainable alerts and prevent duplicate alerts.
- Goal: Reduce alert flooding and support human review.

## 7. Case Management
- Prompt: Create operational cases from alerts and support assignment, notes, status updates, resolution, and audit timeline.
- Goal: Track human response from alert to closure.

## 8. Frontend
- Prompt: Build a React dashboard showing agents, balances, forecasts, alerts, and cases.
- Prompt: Add an Inject Full Demo button.
- Goal: Demonstrate the full workflow from the frontend.

## 9. Demo and Testing
- Prompt: Add fresh demo scenarios for liquidity crisis and anomaly burst.
- Goal: Make the system reliably demonstrable at any time.

## 10. Documentation
- Prompt: Create README and judge explanation.
- Goal: Make the project easy to run, understand, and present.