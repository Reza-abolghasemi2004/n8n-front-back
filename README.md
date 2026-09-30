# NexusFlow: n8n Digital Marketing Automation Dashboard

A simple, production-ready internal **Flask Admin Dashboard** for managing project/intake records stored in **PostgreSQL** and processed by **n8n** automation workflows.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [n8n Workflow Setup](#n8n-workflow-setup)
- [Running Without Docker (Local Development)](#running-without-docker-local-development)
- [Routes and Endpoints](#routes-and-endpoints)
- [Usage](#usage)
- [Reverse Proxy, Domain and HTTPS](#reverse-proxy-domain-and-https)
- [Logs](#logs)
- [Troubleshooting](#troubleshooting)
- [Production Checklist](#production-checklist)
- [Contributing](#contributing)
- [License](#license)
- [Author](#author)

---

## Overview

NexusFlow is an internal admin platform for digital marketing operations. Administrators record project intake requests, trigger automation workflows in n8n, and review the execution telemetry and generated outputs, all from one dashboard.

**Key features**

- Admin-only dashboard with secure login (no public registration, no customer portal, no RBAC)
- Project intake CRUD with filters, status updates, and n8n workflow triggers
- Execution tracking with n8n API status sync
- Output review for n8n-generated deliverables
- PostgreSQL 16 with `JSONB` fields for flexible service, attachment, and payload data
- Modern dark SaaS UI with toast notifications, loading states, and confirmations
- Fully containerized with Docker Compose and served by Gunicorn

---

## Architecture

```text
Admin
   │
   ▼
Flask Admin Dashboard (Gunicorn)
   │        ▲
   │        │  trigger workflow / sync execution (n8n API + webhooks)
   ▼        │
PostgreSQL 16  ◄────────  n8n
                          │
                          ▼
            External services (email, Google Sheets,
                   Telegram, other APIs...)
```

- **Flask** manages and displays project intake data, authentication, execution telemetry, and generated outputs.
- **PostgreSQL** is the primary relational + `JSONB` database shared by Flask and n8n on an internal Docker network.
- **n8n** runs the automation workflows, reads project records from PostgreSQL, and writes execution statuses and generated outputs back to PostgreSQL.
- **Single user type:** Administrator (`AdminUser`).

**Flow**

1. The admin creates or updates a project in the dashboard.
2. Flask stores it in PostgreSQL and triggers an **n8n workflow**.
3. n8n reads the project, runs the automation, and performs actions in external services.
4. n8n writes execution status and generated outputs back to PostgreSQL.
5. The dashboard displays the results, and executions can be re-synced through the n8n API.

---

## Tech Stack

| Layer      | Technology                                                   |
| ---------- | ------------------------------------------------------------ |
| Frontend   | Server-rendered Jinja2 templates, HTML5, CSS3, vanilla JS    |
| Backend    | Python 3.10+, Flask, Gunicorn                                |
| Database   | PostgreSQL 16 (with `JSONB`)                                 |
| ORM / Migrations | SQLAlchemy, Flask-Migrate (Alembic)                    |
| Auth / Security  | Flask-Login, Flask-WTF (CSRF), Werkzeug password hashing |
| Automation | n8n                                                          |
| Infra      | Docker, Docker Compose                                       |
| Testing    | Pytest (against PostgreSQL)                                  |

---

## Project Structure

```text
.
├── app/
│   ├── __init__.py              # Flask application factory, Jinja filters, error handlers
│   ├── config.py                # Environment-driven configuration (PostgreSQL, CSRF, cookies, n8n)
│   ├── extensions.py            # SQLAlchemy, Flask-Migrate, Flask-Login, CSRFProtect
│   ├── cli.py                   # Flask CLI commands (`flask create-admin`, `flask seed-demo`)
│   ├── forms.py                 # Flask-WTF server-side validated forms
│   │
│   ├── routes/
│   │   ├── auth.py              # /login and /logout routes
│   │   ├── dashboard.py         # / (overview metrics, recent projects & executions) and /health
│   │   ├── projects.py          # /projects CRUD, filters, status updates, n8n triggers
│   │   ├── executions.py        # /executions list, detail, and n8n API sync
│   │   └── outputs.py           # /outputs list, detail, status review, and logging
│   │
│   ├── models/
│   │   ├── user.py              # AdminUser model (Werkzeug password hashing + Flask-Login)
│   │   ├── project.py           # Project intake model with JSONB services & attachments
│   │   ├── execution.py         # Execution model tracking n8n workflow runs & JSONB payloads
│   │   └── output.py            # Output model storing n8n deliverables & JSONB data
│   │
│   ├── integrations/
│   │   └── n8n.py               # trigger_workflow(), get_execution(), sync_execution_status()
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── errors/
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── projects/
│   │   ├── executions/
│   │   └── outputs/
│   │
│   └── static/
│       ├── css/style.css        # Modern dark SaaS UI design system
│       └── js/app.js            # Toast notifications, loading states, confirmations
│
├── migrations/                  # Flask-Migrate / Alembic PostgreSQL migrations
├── n8n/
│   └── workflows/
│       ├── project_intake_automation.json
│       └── README.md
│
├── tests/                       # Pytest test suite running against PostgreSQL
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── run.py
└── README.md
```

---

## Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose (recommended way to run everything)
- [Git](https://git-scm.com/)

For running without Docker (local development) you will also need:

- [Python 3.10+](https://www.python.org/downloads/)
- [PostgreSQL 16](https://www.postgresql.org/download/)
- [Node.js 18+](https://nodejs.org/) (to run n8n via npm)

---

## Installation and Setup

### Step 1: Clone the repository

```bash
git clone https://github.com/Reza-abolghasemi2004/your-repo.git
cd your-repo
```

### Step 2: Create `.env`

```bash
cp .env.example .env
```

Open `.env` and update the following values before starting the stack:

- `POSTGRES_PASSWORD`: Set a strong, unique password for PostgreSQL.
- `DATABASE_URL`: Replace `CHANGE_ME` with the exact `POSTGRES_PASSWORD` you chose:
  ```env
  DATABASE_URL=postgresql+psycopg://agent_platform:YOUR_STRONG_PASSWORD@postgres:5432/agent_platform
  ```
- `SECRET_KEY`: Generate a strong random secret key (e.g. `openssl rand -hex 32`).
- `N8N_API_KEY`: Your n8n API key (generated inside n8n under **Settings → n8n API**).
- `N8N_ENCRYPTION_KEY`: A random 32-character encryption key for n8n credentials.
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`: Credentials for bootstrapping the initial administrator account.

> ⚠️ Never commit your real `.env` file. Make sure it is listed in `.gitignore`.

### Step 3: Start the services

Build and launch `flask`, `postgres`, and `n8n` in detached mode:

```bash
docker compose up -d --build
```

All services communicate over the internal Docker network (`platform_net`) using service hostnames (`postgres:5432`, `n8n:5678`). PostgreSQL is **not** exposed to the public host network.

### Step 4: Run database migrations

```bash
docker compose exec flask flask db upgrade
```

If you modify models in the future, generate and apply new migrations with:

```bash
docker compose exec flask flask db migrate -m "Describe schema change"
docker compose exec flask flask db upgrade
```

### Step 5: Create the first admin account

```bash
docker compose exec flask flask create-admin \
  --username admin \
  --email admin@example.com \
  --password "YourStrongPasswordHere"
```

*(Optional)* Populate sample projects, executions, and outputs for testing:

```bash
docker compose exec flask flask seed-demo
```

### Step 6: Configure n8n and import workflows

See [n8n Workflow Setup](#n8n-workflow-setup) below.

---

## n8n Workflow Setup

1. Open n8n at <http://localhost:5678> (or your configured n8n domain) and complete the initial owner setup.
2. Go to **Settings → n8n API**, create an API key, and set `N8N_API_KEY` in `.env`, then apply it with:
   ```bash
   docker compose up -d flask
   ```
3. In n8n, create a **Postgres** credential named `Agent Platform PostgreSQL`:
   - **Host:** `postgres`
   - **Database:** `agent_platform`
   - **User:** `agent_platform`
   - **Password:** your `POSTGRES_PASSWORD` from `.env`
   - **Port:** `5432`
4. Import the workflow from `n8n/workflows/project_intake_automation.json` (**Workflows → Import from File**).
5. Select your `Agent Platform PostgreSQL` credential on the Postgres nodes.
6. Configure credentials for any external services the workflow uses (email, Google Sheets, Telegram, etc.).
7. Open the **Webhook** node, copy the **Production URL**, and set it in your `.env` if your configuration uses a webhook URL.
8. **Activate** the workflow using the toggle in the top-right corner.

> Use the **Test URL** while developing and the **Production URL** once the workflow is active.

---

## Running Without Docker (Local Development)

**1. Start PostgreSQL** and create the `agent_platform` database and user, then point `DATABASE_URL` in `.env` at `localhost` instead of `postgres`.

**2. Start n8n**

```bash
npm install n8n -g
n8n start
```

n8n will be available at <http://localhost:5678>.

**3. Set up and start Flask**

```bash
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
flask db upgrade
flask create-admin --username admin --email admin@example.com --password "YourStrongPasswordHere"
python run.py
```

The dashboard will run at <http://localhost:5000>.

---

## Routes and Endpoints

| Area       | Route          | Description                                                   |
| ---------- | -------------- | ------------------------------------------------------------- |
| Auth       | `/login`, `/logout` | Administrator authentication                             |
| Dashboard  | `/`            | Overview metrics, recent projects and executions              |
| Health     | `/health`      | Health check                                                  |
| Projects   | `/projects`    | CRUD, filters, status updates, n8n workflow triggers          |
| Executions | `/executions`  | List, detail, and n8n API status sync                         |
| Outputs    | `/outputs`     | List, detail, status review, and logging                      |

---

## Usage

1. Log in to the dashboard with your admin credentials.
2. Create a project intake record (or use `flask seed-demo` for sample data).
3. Trigger the n8n workflow from the project page.
4. Follow progress under **Executions** and sync status from the n8n API when needed.
5. Review and approve generated deliverables under **Outputs**.

*(Add screenshots here)*

```text
![Dashboard](docs/dashboard.png)
```

---

## Reverse Proxy, Domain and HTTPS

For production deployment behind Nginx, Caddy, or Traefik:

1. Proxy HTTPS traffic (`443`) for your admin domain (e.g. `admin.yourdomain.com`) to `http://127.0.0.1:5000`.
2. Set `SESSION_COOKIE_SECURE=true` in `.env` so session cookies are only transmitted over HTTPS.
3. Keep port `5432` unexposed (handled automatically by `docker-compose.yml`).

---

## Logs

Tail live logs for each service:

```bash
docker compose logs -f flask
docker compose logs -f postgres
docker compose logs -f n8n
```

---

## Troubleshooting

| Problem | Possible solution |
| ------- | ----------------- |
| **Cannot log in** | Make sure you created an admin with `flask create-admin` |
| **Database errors / missing tables** | Run `docker compose exec flask flask db upgrade` |
| **Flask can't connect to PostgreSQL** | Check that `DATABASE_URL` uses the same password as `POSTGRES_PASSWORD` and host `postgres` (Docker) |
| **404 on n8n webhook** | Check that the workflow is **active** and the URL/path is correct (Production vs Test URL) |
| **n8n sync fails** | Verify `N8N_API_KEY` is set, then run `docker compose up -d flask` |
| **Connection refused** | Verify all containers are running with `docker compose ps` |
| **Login works but session drops over HTTP** | `SESSION_COOKIE_SECURE=true` requires HTTPS; disable it for local testing only |
| **Module not found (local dev)** | Activate the virtual environment and run `pip install -r requirements.txt` |

---

## Production Checklist

```text
[ ] .env configured
[ ] Strong database password
[ ] Strong SECRET_KEY
[ ] Admin account created
[ ] Database migration completed
[ ] PostgreSQL persistent volume
[ ] n8n persistent volume
[ ] HTTPS configured
[ ] PostgreSQL not publicly exposed
[ ] Flask running with Gunicorn
```

---

## Contributing

1. Fork the project
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Author

**Reza Abolghasemi** – [GitHub](https://github.com/Reza-abolghasemi2004) · [LinkedIn](https://www.linkedin.com/in/reza-abolghasemi2004/)
