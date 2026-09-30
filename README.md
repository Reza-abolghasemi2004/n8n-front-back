# NexusFlow — Flask Admin Dashboard for n8n Automation

A simple, production-ready internal **Flask Admin Dashboard** for managing project/intake records stored in **PostgreSQL** and processed by **n8n** automation workflows.

---

## Architecture

The platform consists of only three core components:

```text
Admin
   │
   ▼
Flask Admin Dashboard (Gunicorn)
   │
   ▼
PostgreSQL 16
   ▲
   │
  n8n
```

- **Flask** manages and displays project intake data, authentication, execution telemetry, and generated outputs.
- **PostgreSQL** is the primary relational + `JSONB` database shared by Flask and n8n on an internal Docker network.
- **n8n** runs the automation workflows, reads project records from PostgreSQL, and writes execution statuses and generated outputs back to PostgreSQL.
- **Single User Type:** Administrator (`AdminUser`). There is no public registration, no customer portal, no RBAC, and no microservice orchestrator.

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
│   │   ├── dashboard.py         # / (Overview metrics, recent projects & executions) and /health
│   │   ├── projects.py          # /projects CRUD, filters, status updates, n8n triggers
│   │   ├── executions.py        # /executions list, detail, and n8n API sync
│   │   └── outputs.py           # /outputs list, detail, status review, and logging
│   │
│   ├── models/
│   │   ├── user.py              # AdminUser model (Werkzeug password hashing + Flask-Login)
│   │   ├── project.py           # Project intake model with PostgreSQL JSONB services & attachments
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

## Manual Setup Instructions

### Step 1 — Create `.env`

Copy the example environment file:

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
- `N8N_API_KEY`: Set your n8n API key (generated inside n8n under **Settings → n8n API**).
- `N8N_ENCRYPTION_KEY`: Set a random 32-character encryption key for n8n credentials.
- `ADMIN_USERNAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`: Credentials for bootstrapping the initial administrator account.

---

### Step 2 — Start the Services

Build and launch `flask`, `postgres`, and `n8n` in detached mode:

```bash
docker compose up -d --build
```

All services communicate over the internal Docker network (`platform_net`) using service hostnames (`postgres:5432`, `n8n:5678`). PostgreSQL is **not** exposed to the public host network.

---

### Step 3 — Run Database Migrations

Apply the Alembic / Flask-Migrate schema migrations to PostgreSQL:

```bash
docker compose exec flask flask db upgrade
```

If you modify models in the future, generate and apply new migrations with:

```bash
docker compose exec flask flask db migrate -m "Describe schema change"
docker compose exec flask flask db upgrade
```

---

### Step 4 — Create the First Admin Account

Create your administrator account using the built-in Flask CLI command:

```bash
docker compose exec flask flask create-admin \
  --username admin \
  --email admin@example.com \
  --password "YourStrongPasswordHere"
```

*(Optional)* To populate sample projects, executions, and outputs for testing:

```bash
docker compose exec flask flask seed-demo
```

---

### Step 5 — Configure n8n and Import Workflows

1. Open n8n at `http://localhost:5678` (or your configured n8n domain) and complete the initial owner setup.
2. Go to **Settings → n8n API**, create an API key, and set `N8N_API_KEY` in `.env` (then run `docker compose up -d flask`).
3. In n8n, create a **Postgres** credential named `Agent Platform PostgreSQL`:
   - **Host:** `postgres`
   - **Database:** `agent_platform`
   - **User:** `agent_platform`
   - **Password:** *(your `POSTGRES_PASSWORD` from `.env`)*
   - **Port:** `5432`
4. Import the workflow from `n8n/workflows/project_intake_automation.json` (**Workflows → Import from File**), select your `Agent Platform PostgreSQL` credential on the Postgres nodes, and toggle the workflow to **Active**.

---

### Step 6 — Configure Reverse Proxy / Domain / HTTPS

For production deployment behind Nginx, Caddy, or Traefik:

1. Proxy HTTPS traffic (`443`) for your admin domain (e.g. `admin.yourdomain.com`) to `http://127.0.0.1:5000`.
2. Set `SESSION_COOKIE_SECURE=true` in `.env` so session cookies are only transmitted over HTTPS.
3. Keep port `5432` unexposed (handled automatically by `docker-compose.yml`).

---

### Step 7 — Checking Logs

Tail live logs for each service:

```bash
docker compose logs -f flask
docker compose logs -f postgres
docker compose logs -f n8n
```

---

### Step 8 — Production Checklist

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
