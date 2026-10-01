import logging
from datetime import datetime, timezone
from typing import Any
import requests
from flask import current_app
from app.extensions import db
from app.models.execution import Execution
from app.models.output import Output
from app.models.project import Project

logger = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _get_n8n_settings() -> dict[str, Any]:
    """Read n8n connection parameters from Flask config / environment."""
    base_url = current_app.config.get("N8N_BASE_URL", "http://n8n:5678").rstrip("/")
    api_key = current_app.config.get("N8N_API_KEY", "")
    webhook_path = current_app.config.get("N8N_WEBHOOK_PATH", "/webhook/project-intake")
    timeout = int(current_app.config.get("N8N_TIMEOUT", 15))
    return {
        "base_url": base_url,
        "api_key": api_key,
        "webhook_path": webhook_path,
        "timeout": timeout,
    }


def _build_headers(api_key: str | None = None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    if api_key and api_key != "CHANGE_ME":
        headers["X-N8N-API-KEY"] = api_key
    return headers


def trigger_workflow(
    project: Project,
    workflow_path: str | None = None,
    trigger_source: str = "manual",
    extra_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Trigger an n8n workflow for a given Project.

    Uses `project.id` as the primary reference between Flask and n8n.
    Creates an Execution record in PostgreSQL, dispatches the webhook payload
    to n8n, and updates the Execution record with n8n's response.
    """
    settings = _get_n8n_settings()
    path = (workflow_path or settings["webhook_path"]).lstrip("/")
    webhook_url = f"{settings['base_url']}/{path}"

    payload = project.to_n8n_payload()
    if extra_payload:
        payload.update(extra_payload)

    execution = Execution(
        project_id=project.id,
        workflow_name="Project Intake Automation",
        trigger_source=trigger_source,
        status="running",
        payload=payload,
        started_at=utc_now(),
    )
    db.session.add(execution)
    db.session.flush()

    payload["execution_id"] = execution.id
    execution.payload = dict(payload)

    try:
        response = requests.post(
            webhook_url,
            json=payload,
            headers=_build_headers(settings["api_key"]),
            timeout=settings["timeout"],
        )
        response.raise_for_status()

        try:
            resp_json = response.json()
            if not isinstance(resp_json, dict):
                resp_json = {"result": resp_json}
        except ValueError:
            resp_json = {"raw_response": response.text[:2000]}

        execution.response_data = resp_json
        execution.n8n_execution_id = str(
            resp_json.get("execution_id")
            or resp_json.get("n8n_execution_id")
            or resp_json.get("executionId")
            or response.headers.get("X-N8N-Execution-Id", "")
        ) or execution.n8n_execution_id

        if resp_json.get("workflow_id"):
            execution.workflow_id = str(resp_json["workflow_id"])
        if resp_json.get("workflow_name"):
            execution.workflow_name = str(resp_json["workflow_name"])

        returned_status = str(resp_json.get("status", "running")).lower()
        if returned_status in ("success", "completed", "done"):
            execution.status = "success"
            execution.finished_at = utc_now()
            if project.status in ("New", "Validated", "Queued"):
                project.status = "Completed"
        elif returned_status in ("failed", "error"):
            execution.status = "failed"
            execution.error_message = str(resp_json.get("error") or "Workflow reported failure.")
            execution.finished_at = utc_now()
            project.status = "Failed"
        else:
            execution.status = "running"
            if project.status in ("New", "Validated"):
                project.status = "In Progress"

        # If the workflow synchronously returned an output block, persist it
        output_block = resp_json.get("output")
        if isinstance(output_block, dict) and output_block.get("title"):
            output = Output(
                project_id=project.id,
                execution_id=execution.id,
                title=str(output_block.get("title")),
                output_type=str(output_block.get("output_type", "report")),
                summary=output_block.get("summary"),
                content=output_block.get("content"),
                data=output_block.get("data") if isinstance(output_block.get("data"), dict) else {},
                status=str(output_block.get("status", "generated")),
            )
            db.session.add(output)

        db.session.commit()
        return {
            "ok": True,
            "execution": execution,
            "response": resp_json,
            "error": None,
        }

    except requests.RequestException as exc:
        logger.warning("n8n workflow trigger failed for project %s: %s", project.id, exc)
        execution.status = "failed"
        execution.error_message = f"Unable to reach n8n webhook ({webhook_url}): {exc}"
        execution.response_data = {
            "webhook_url": webhook_url,
            "error": str(exc),
        }
        execution.finished_at = utc_now()
        db.session.commit()
        return {
            "ok": False,
            "execution": execution,
            "response": None,
            "error": str(exc),
        }


def get_execution(n8n_execution_id: str) -> dict[str, Any]:
    """
    Fetch execution details from the n8n REST API (/api/v1/executions/<id>).
    """
    if not n8n_execution_id:
        return {
            "ok": False,
            "data": None,
            "error": "No n8n_execution_id provided.",
        }

    settings = _get_n8n_settings()
    url = f"{settings['base_url']}/api/v1/executions/{n8n_execution_id}"

    try:
        response = requests.get(
            url,
            headers=_build_headers(settings["api_key"]),
            timeout=settings["timeout"],
        )
        response.raise_for_status()
        data = response.json()

        raw_status = str(data.get("status") or "").lower()
        finished = bool(data.get("finished"))
        if raw_status in ("success",) or (finished and raw_status not in ("error", "failed", "canceled")):
            normalized_status = "success"
        elif raw_status in ("error", "failed", "crashed"):
            normalized_status = "failed"
        elif raw_status in ("canceled", "cancelled"):
            normalized_status = "canceled"
        elif raw_status in ("waiting", "new"):
            normalized_status = "queued"
        else:
            normalized_status = "running"

        return {
            "ok": True,
            "status": normalized_status,
            "finished": finished,
            "started_at": data.get("startedAt"),
            "stopped_at": data.get("stoppedAt"),
            "workflow_id": str(data.get("workflowId") or ""),
            "data": data,
            "error": None,
        }
    except requests.RequestException as exc:
        logger.warning("Failed to fetch n8n execution %s: %s", n8n_execution_id, exc)
        return {
            "ok": False,
            "status": None,
            "data": None,
            "error": str(exc),
        }


def sync_execution_status(execution: Execution) -> dict[str, Any]:
    """
    Poll n8n for the latest status of an Execution record and update PostgreSQL.
    """
    if not execution.n8n_execution_id:
        return {
            "ok": False,
            "execution": execution,
            "error": "Execution does not have an external n8n_execution_id to sync.",
        }

    result = get_execution(execution.n8n_execution_id)
    if not result["ok"]:
        return {
            "ok": False,
            "execution": execution,
            "error": result["error"],
        }

    execution.status = result["status"]
    if result.get("workflow_id"):
        execution.workflow_id = result["workflow_id"]
    if isinstance(result.get("data"), dict):
        execution.response_data = result["data"]

    if result["status"] in ("success", "failed", "canceled") and not execution.finished_at:
        execution.finished_at = utc_now()

    if execution.project:
        if result["status"] == "success":
            execution.project.status = "Completed"
        elif result["status"] == "failed":
            execution.project.status = "Failed"

    db.session.commit()
    return {
        "ok": True,
        "execution": execution,
        "error": None,
    }


def check_n8n_health() -> dict[str, Any]:
    """Check whether the n8n instance is reachable on the internal network."""
    settings = _get_n8n_settings()
    health_url = f"{settings['base_url']}/healthz"
    try:
        resp = requests.get(health_url, timeout=3)
        return {
            "reachable": resp.status_code < 500,
            "status_code": resp.status_code,
            "base_url": settings["base_url"],
        }
    except requests.RequestException:
        return {
            "reachable": False,
            "status_code": None,
            "base_url": settings["base_url"],
        }
