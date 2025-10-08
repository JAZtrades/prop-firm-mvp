# Prop Firm MVP

This repository contains a minimal **AI‑assisted prop firm MVP**.  It is built to run entirely locally using Docker and includes a FastAPI back end, a simple Next.js front end, a risk engine service, a worker for scheduled jobs, and the necessary database/cache containers.

> **Disclaimer**: this project is a demonstration.  It deals with *simulated* accounts only and **no real money flows**.  Before introducing real funds or production wallet features, consult legal counsel about CFTC/NFA/SEC implications.  Payouts are queued with a settlement window to protect the platform against abuse.

## Features

* FastAPI back end with JWT authentication, CRUD endpoints for users, trades, metrics and payout requests.
* Risk engine implementing a 10 % trailing drawdown, minimum trade/day requirements, consistency checks and payout caps.
* Worker service for daily metrics calculation, payout settlement and probation day counters.
* Simple Next.js 14 front end with React 18 and Tailwind CSS that displays account balances, drawdown, profit to threshold, consistency metrics, trading days and a payout request widget.
* Docker Compose configuration that spins up Postgres 15, Redis and the application services with a single command.
* Unit tests for the risk engine and payout rules using `pytest` and smoke tests for the front end using `playwright`.

## Project Structure

```
prop-firm-mvp/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── accounts.py
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── metrics.py
│   │   ├── payouts.py
│   │   └── trades.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ai_flags.py
│   │   ├── payout_rules.py
│   │   ├── risk_engine.py
│   │   └── simulator.py
│   ├── worker/
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   └── worker.py
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   │   └── page.tsx
│   │   └── auth/
│   │       ├── login/
│   │       │   └── page.tsx
│   │       └── register/
│   │           └── page.tsx
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── MetricCard.tsx
│   │   └── PayoutModal.tsx
│   ├── package.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   └── tsconfig.json
├── tests/
│   ├── backend/
│   │   ├── __init__.py
│   │   └── test_risk_engine.py
│   └── frontend/
│       ├── __init__.py
│       └── test_smoke.py
├── docker-compose.yml
├── .env.example
└── .gitignore
```

## Prerequisites

* Docker and Docker Compose
* Node 16 or later (only if you wish to run the front end outside of Docker)

## Running the stack

1. **Clone this repo** and create a copy of the environment file:

   ```bash
   cp .env.example .env
   ```

2. **Build and start the services** using Docker Compose:

   ```bash
   docker compose up -d --build
   ```

   This command builds the back end and front end images, starts Postgres and Redis, runs database migrations on first boot and launches the worker.

3. **Apply database migrations** (if you add new models) via Alembic:

   ```bash
   docker exec -it prop-firm-backend alembic upgrade head
   ```

4. **Seed a demo account** using the simulator.  Run the following from within the back end container:

   ```bash
   docker exec -it prop-firm-backend python -m app.backend.services.simulator --user demo@demo.com --days 22 --hr 0.55
   ```

5. Visit **http://localhost:3000** to see the dashboard.  The API is available on **http://localhost:8000** with the interactive Swagger UI at **/docs**.

## Running Tests

To run the unit tests locally:

```bash
pytest -q
```

For the front end Playwright smoke tests you first need to install the browsers and then run the test script:

```bash
npx playwright install
npm run test:e2e
```

## Security & Compliance

* **Simulated funds only** – no real money moves through this platform.
* Payouts are subject to a 7–14 day settlement window to mitigate fraud and system abuse.
* All account status changes and payout approvals are logged.
* Before deploying a production wallet, consult legal counsel regarding regulatory requirements.
