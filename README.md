# AgentPulse AI

AgentPulse AI is a multi-provider liquidity and risk intelligence platform for Mobile Financial Service (MFS) agents.

It monitors separate provider balances, shared physical cash, recent transaction activity, liquidity pressure, unusual transaction patterns, explainable alerts, and human-led operational case handling.

## Core Problems Addressed

- Predicting provider e-float shortages before they happen
- Detecting physical cash pressure
- Detecting unusual transaction patterns
- Converting alerts into trackable operational cases
- Supporting human review without automatically declaring fraud

## Main Features

- Multi-provider balance monitoring: bKash, Nagad, and Rocket
- Shared physical cash monitoring
- Seven-day synthetic transaction history
- Liquidity forecasting using recent activity and a seven-day same-hour historical baseline
- Anomaly detection:
  - repeated transaction amount
  - high-value transaction burst
  - transaction velocity spike
- Explainable alerts
- Duplicate alert prevention
- Operational case management:
  - create case from alert
  - assign or reassign owner
  - update case status
  - add notes
  - resolve and close case
  - audit timeline
- Full demo scenario injection
- Human-review-based advisory design

## Technology Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Uvicorn

### Frontend

- React
- Vite
- Axios
- Tailwind CSS
- Lucide React

## Project Structure

```text
agentpulse-ai/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── seed.py
│   │   └── services/
│   │       ├── forecasting.py
│   │       ├── anomaly_detection.py
│   │       ├── alert_engine.py
│   │       ├── case_management.py
│   │       └── demo_scenarios.py
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── CaseManagement.jsx
│   │   └── services/
│   │       └── api.js
│   └── package.json
└── README.md
```

## Backend Setup

Open a terminal and go to the backend folder:

```powershell
cd "C:\Users\DUBAI LAPTOP BAZAR\OneDrive\Desktop\SUST ONSITE\agentpulse-ai\backend"
```

Create the virtual environment if needed:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install fastapi uvicorn sqlalchemy pydantic
```

Create or reset the database with seven-day synthetic data:

```powershell
python -m app.seed --reset
```

Start the backend server:

```powershell
uvicorn app.main:app --reload --port 8000
```

Backend URLs:

```text
Health Check: http://127.0.0.1:8000/api/health
Swagger Docs: http://127.0.0.1:8000/docs
```

## Frontend Setup

Open a new terminal:

```powershell
cd "C:\Users\DUBAI LAPTOP BAZAR\OneDrive\Desktop\SUST ONSITE\agentpulse-ai\frontend"
```

Install packages:

```powershell
npm install
```

Start the frontend:

```powershell
npm run dev
```

Open:

```text
http://localhost:5173
```

## Important API Endpoints

### Agents

```text
GET /api/agents
GET /api/agents/{agent_id}
GET /api/agents/{agent_id}/transactions
GET /api/agents/{agent_id}/liquidity-forecast
GET /api/agents/{agent_id}/anomalies
```

### Alerts

```text
POST /api/agents/{agent_id}/generate-alerts
GET /api/alerts
GET /api/alerts/{alert_id}
```

### Cases

```text
POST /api/alerts/{alert_id}/cases
GET /api/cases
GET /api/cases/{case_id}
PATCH /api/cases/{case_id}/assignment
PATCH /api/cases/{case_id}/status
POST /api/cases/{case_id}/notes
```

### Demo Scenarios

```text
POST /api/demo/agents/{agent_id}/liquidity-crisis
POST /api/demo/agents/{agent_id}/anomaly-burst
POST /api/demo/agents/{agent_id}/full-demo
```

## Forecasting Logic

The forecasting service uses:

```text
75% recent transaction pressure
25% seven-day same-hour historical baseline
```

Provider float pressure is estimated from:

```text
cash-in rate - cash-out rate
```

Physical cash pressure is estimated from:

```text
cash-out rate - cash-in rate
```

Estimated shortage time is calculated as:

```text
current available balance / estimated drain rate
```

Severity levels:

```text
30 minutes or less  → Critical
60 minutes or less  → High
120 minutes or less → Medium
More than 120 min   → Low
```

Confidence considers:

- recent transaction count
- historical transaction count
- number of historical days available
- data status
- data freshness

## Demo Flow

Recommended live demo sequence:

```text
1. Select AGT-001
2. Click Inject Full Demo
3. Review updated liquidity forecasts
4. Click Generate Alerts
5. Review saved alerts
6. Click Generate Alerts again
7. Show duplicate alert prevention
8. Create an operational case from an alert
9. Assign a case owner
10. Update case status
11. Add a case note
12. Resolve or close the case
```

## Responsible Design

AgentPulse AI is an advisory system.

It does not:

- declare a customer or agent fraudulent
- automatically block transactions
- move money
- merge provider balances
- replace human decision-making

High-risk findings require human review.

## Data

The project uses synthetic data only.

The dataset includes:

- three demo agents
- three providers
- separate provider balances
- shared physical cash
- seven days of transactions
- labelled anomaly scenarios
- liquidity shortage scenarios
- delayed data scenarios

No real customer or provider data is used.

## Example Judge Explanation

> AgentPulse AI monitors separate MFS provider balances and shared physical cash, compares recent demand with a seven-day same-hour historical baseline, predicts liquidity shortages, detects unusual transaction patterns, creates explainable alerts, and supports human-led case handling. It uses synthetic data and does not automatically declare fraud or take financial action.

## GitHub Notes

Recommended `.gitignore` entries:

```gitignore
backend/.venv/
frontend/node_modules/
backend/agentpulse.db
*.pyc
__pycache__/
.env
dist/
```

Before pushing:

```powershell
git add .
git commit -m "Final AgentPulse AI submission"
git push origin main
```

## Current Status

The project is ready for final submission with:

- working backend
- working frontend
- seven-day synthetic dataset
- liquidity forecasting
- anomaly detection
- alert generation
- duplicate prevention
- case management
- demo scenario injection
- explainable and responsible AI design
