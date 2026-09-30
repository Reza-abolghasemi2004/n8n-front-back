# n8n Workflows

This directory contains exportable n8n workflows that process project intakes stored in PostgreSQL.

## Included Workflow

- **`project_intake_automation.json`**
  1. **Project Intake Webhook (`POST /webhook/project-intake`)**: Receives `project_id`, `intake_id`, and `execution_id` from Flask (`app/integrations/n8n.py`).
  2. **Read Project from PostgreSQL**: Reads the full project record from the `projects` table using `project_id`.
  3. **Process Intake & Build Output**: Processes the intake scope and constructs the deliverable report and JSONB telemetry.
  4. **Write Output & Status to PostgreSQL**: Inserts the generated result into `outputs`, updates `projects.status`, and updates `executions.status` in PostgreSQL.
  5. **Respond to Flask**: Returns execution metadata to the Flask webhook caller.

## How to Import in n8n

1. Open the n8n editor (`http://localhost:5678`).
2. Create a **PostgreSQL Credential** named `Agent Platform PostgreSQL` with:
   - **Host:** `postgres` (internal Docker network hostname — do NOT use `localhost`)
   - **Port:** `5432`
   - **Database:** value of `POSTGRES_DB` (default `agent_platform`)
   - **User:** value of `POSTGRES_USER` (default `agent_platform`)
   - **Password:** value of `POSTGRES_PASSWORD`
3. Go to **Workflows → Import from File** and select `n8n/workflows/project_intake_automation.json`.
4. Attach your PostgreSQL credential to the two Postgres nodes and toggle the workflow to **Active**.
