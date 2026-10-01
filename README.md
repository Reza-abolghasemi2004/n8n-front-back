# NexusFlow — Flask Admin Dashboard + PostgreSQL + n8n + Nginx

Production-ready internal **Flask Admin Dashboard** for managing project/intake records stored in **PostgreSQL 16**, processed by **n8n**, and served behind a containerized **Nginx Reverse Proxy**.

- **Target Server IP:** `81.12.50.30`
- **Target Domain:** `http://n8n.rezaabolghasemi.ir`

---

## Architecture

```text
Internet (http://n8n.rezaabolghasemi.ir / 81.12.50.30)
   │
   ▼
Nginx Container (Port 80 / 443)
   ├── /                 ──► Flask Admin Dashboard (Gunicorn :5000)
   └── /webhook/*        ──► n8n Automation Engine (:5678)
                                 │
                                 ▼
                         PostgreSQL 16 (:5432, internal only)
```

All 4 containers (`nginx`, `flask`, `postgres`, `n8n`) run on the shared internal Docker network `platform_net`.

---

## Pre-Configured Credentials (`.env`)

The `.env` file is already pre-configured with strong production keys and passwords for `81.12.50.30` and `n8n.rezaabolghasemi.ir`:

| Variable | Configured Value |
| :--- | :--- |
| **Server IP** | `81.12.50.30` |
| **Domain** | `n8n.rezaabolghasemi.ir` |
| **Admin Dashboard URL** | `http://n8n.rezaabolghasemi.ir` (or `http://81.12.50.30`) |
| **n8n Editor URL** | `http://n8n.rezaabolghasemi.ir:5678` (or `http://81.12.50.30:5678`) |
| **Admin Username** | `admin` |
| **Admin Email** | `admin@n8n.rezaabolghasemi.ir` |
| **Admin Password** | `Reza@Admin2026!#` |
| **PostgreSQL Host (internal)** | `postgres` |
| **PostgreSQL Port** | `5432` |
| **PostgreSQL Database** | `agent_platform` |
| **PostgreSQL User** | `agent_platform` |
| **PostgreSQL Password** | `Nx9vK4mP8qR2wL7xJ5tB3zF6hY1cD0sA` |
| **Flask `SECRET_KEY`** | `8f4e2a9c7b1d6e3f5a0c8b2d4e6f1a3c9b7e5d2f4a8c1b6e3d9f0a7c5b2e4d8f` |
| **n8n Encryption Key** | `k9P2mX7vL4qR8nW1zB5tF3yH6jC0dG8s` |

---

## Project Structure

```text
.
├── app/
│   ├── __init__.py              # Flask factory + ProxyFix for Nginx reverse proxy
│   ├── config.py                # PostgreSQL, session security, CSRF, n8n config
│   ├── extensions.py            # SQLAlchemy, Flask-Migrate, Flask-Login, CSRFProtect
│   ├── cli.py                   # CLI commands (`flask create-admin`, `flask seed-demo`)
│   ├── forms.py                 # Server-side validated WTForms
│   ├── models/                  # AdminUser, Project, Execution, Output (PostgreSQL JSONB)
│   ├── integrations/n8n.py      # trigger_workflow(), get_execution(), sync_execution_status()
│   ├── routes/                  # auth, dashboard, projects, executions, outputs
│   ├── templates/               # Modern Dark SaaS Jinja2 templates
│   └── static/                  # CSS & JS assets
├── nginx/
│   ├── nginx.conf               # Main Nginx worker, gzip & buffer configuration
│   ├── conf.d/default.conf      # Reverse proxy for n8n.rezaabolghasemi.ir & 81.12.50.30
│   └── ssl/                     # Directory for SSL certificates (fullchain.pem / privkey.pem)
├── migrations/                  # Flask-Migrate / Alembic database migrations
├── n8n/workflows/               # Exported n8n workflow JSON (`project_intake_automation.json`)
├── tests/                       # Pytest test suite
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── requirements.txt
└── run.py
```

---

## Complete Server Deployment Guide (`81.12.50.30` / `n8n.rezaabolghasemi.ir`)

### Step 1 — DNS Check

Make sure your DNS `A` record points to your server IP:

- **Host:** `n8n.rezaabolghasemi.ir`
- **Type:** `A`
- **Value:** `81.12.50.30`

---

### Step 2 — SSH into the Server & Clone the Repository

```bash
ssh root@81.12.50.30

git clone https://github.com/Reza-abolghasemi2004/n8n-front-back.git
cd n8n-front-back
git checkout arena/01a0f116-n8n-front-back
```

*(Note: `.env` and `nginx/conf.d/default.conf` are already pre-configured in the repository—no manual editing is required.)*

---

### Step 3 — Build and Start All Containers (`nginx`, `flask`, `postgres`, `n8n`)

```bash
docker compose up -d --build
```

Verify that all 4 containers are running:

```bash
docker compose ps
```

---

### Step 4 — Run PostgreSQL Database Migrations

Create all database tables (`admin_users`, `projects`, `executions`, `outputs`) and indexes:

```bash
docker compose exec flask flask db upgrade
```

---

### Step 5 — Create the Admin Account & Optional Demo Data

Run the `create-admin` command (it automatically uses `ADMIN_USERNAME=admin`, `ADMIN_EMAIL=admin@n8n.rezaabolghasemi.ir`, and `ADMIN_PASSWORD=Reza@Admin2026!#` from `.env`):

```bash
docker compose exec flask flask create-admin
```

*(Optional)* Seed sample projects, executions, and outputs so the dashboard is populated immediately:

```bash
docker compose exec flask flask seed-demo
```

Now open your browser and sign in to the **Admin Dashboard**:

- **URL:** [http://n8n.rezaabolghasemi.ir](http://n8n.rezaabolghasemi.ir) *(or `http://81.12.50.30`)*
- **Username:** `admin` *(or `admin@n8n.rezaabolghasemi.ir`)*
- **Password:** `Reza@Admin2026!#`

---

### Step 6 — Configure n8n & Import the Workflow

1. Open n8n in your browser at:
   - [http://n8n.rezaabolghasemi.ir:5678](http://n8n.rezaabolghasemi.ir:5678) *(or `http://81.12.50.30:5678`)*
2. Complete the initial n8n owner setup screen.
3. In n8n, go to **Credentials → Add Credential → Postgres** and enter:
   - **Credential Name:** `Agent Platform PostgreSQL`
   - **Host:** `postgres` *(internal Docker hostname — do NOT use `localhost`)*
   - **Database:** `agent_platform`
   - **User:** `agent_platform`
   - **Password:** `Nx9vK4mP8qR2wL7xJ5tB3zF6hY1cD0sA`
   - **Port:** `5432`
   - **SSL:** `Disable`
4. Go to **Workflows → Import from File** and import:
   - `n8n/workflows/project_intake_automation.json`
5. Select the `Agent Platform PostgreSQL` credential inside the two Postgres nodes and switch the workflow toggle in the top-right corner to **Active**.
6. *(Optional)* If you generate an n8n API key under **Settings → n8n API**, update `N8N_API_KEY` in `.env` and run `docker compose up -d flask`.

---

### Step 7 — Monitoring & Logs on the Server

Check real-time container logs at any time:

```bash
docker compose logs -f nginx
docker compose logs -f flask
docker compose logs -f postgres
docker compose logs -f n8n
```

Restart Nginx after any config changes in `./nginx/conf.d/default.conf`:

```bash
docker compose restart nginx
```

---

### Step 8 — Production Checklist

```text
[x] .env pre-configured with strong passwords & keys
[x] Nginx container configured in ./nginx/conf.d/default.conf for 81.12.50.30 & n8n.rezaabolghasemi.ir
[x] PostgreSQL persistent volume (postgres_data)
[x] n8n persistent volume (n8n_data)
[x] PostgreSQL isolated on internal Docker network (not publicly exposed)
[x] Flask running with Gunicorn behind Nginx reverse proxy
[ ] Run `docker compose up -d --build` on 81.12.50.30
[ ] Run `docker compose exec flask flask db upgrade`
[ ] Run `docker compose exec flask flask create-admin`
[ ] Import & activate workflow in n8n (`n8n/workflows/project_intake_automation.json`)
```
