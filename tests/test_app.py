from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch
import requests
from app.extensions import db
from app.integrations.n8n import get_execution, sync_execution_status, trigger_workflow
from app.models.execution import Execution
from app.models.output import Output
from app.models.project import Project


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"
    assert resp.get_json()["database"] is True


def test_unauthenticated_redirects_to_login(client):
    for path in ["/", "/projects", "/projects/create", "/executions", "/outputs"]:
        resp = client.get(path)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_login_and_logout(client):
    # Invalid login
    bad_resp = client.post(
        "/login",
        data={"identifier": "admin", "password": "wrong-password"},
        follow_redirects=True,
    )
    assert bad_resp.status_code == 200
    assert b"Invalid credentials" in bad_resp.data

    # Valid login
    good_resp = client.post(
        "/login",
        data={"identifier": "admin@example.com", "password": "StrongPass123!"},
        follow_redirects=True,
    )
    assert good_resp.status_code == 200
    assert b"Platform Overview" in good_resp.data

    # Logout
    logout_resp = client.post("/logout", follow_redirects=True)
    assert logout_resp.status_code == 200
    assert b"Sign In to Dashboard" in logout_resp.data


def test_project_crud_and_postgresql_jsonb_filters(auth_client, app):
    # Create project
    create_resp = auth_client.post(
        "/projects/create",
        data={
            "intake_id": "INT-recgWMUE97Yjoxy4E",
            "company_name": "Test Company",
            "website": "https://testcompany.example.com",
            "industry": "Technology",
            "contact_name": "Alex Rivera",
            "email": "alex@testcompany.example.com",
            "phone": "+1 555-0100",
            "country": "United States",
            "monthly_budget": "4500.00",
            "goal": "Generate Leads",
            "services": ["Content", "SEO"],
            "custom_services": "Outbound Automation",
            "priority": "High",
            "deadline": "2026-08-24",
            "attachments_text": "Brief.pdf | https://example.com/brief.pdf | pdf",
            "notes": "Initial intake notes.",
            "status": "Validated",
        },
        follow_redirects=True,
    )
    assert create_resp.status_code == 200
    assert b"Test Company" in create_resp.data
    assert b"INT-recgWMUE97Yjoxy4E" in create_resp.data
    assert b"Outbound Automation" in create_resp.data

    with app.app_context():
        project = Project.query.filter_by(intake_id="INT-recgWMUE97Yjoxy4E").first()
        assert project is not None
        assert project.company_name == "Test Company"
        assert project.monthly_budget == Decimal("4500.00")
        assert "Content" in project.services
        assert "Outbound Automation" in project.services
        assert project.attachments[0]["name"] == "Brief.pdf"
        project_id = project.id

    # Filter projects list by JSONB service
    list_resp = auth_client.get("/projects?service=Content&status=Validated&priority=High")
    assert list_resp.status_code == 200
    assert b"Test Company" in list_resp.data

    # Filter by non-matching service
    empty_resp = auth_client.get("/projects?service=Paid+Ads")
    assert empty_resp.status_code == 200
    assert b"No matching projects found" in empty_resp.data

    # Edit project
    edit_resp = auth_client.post(
        f"/projects/{project_id}/edit",
        data={
            "intake_id": "INT-recgWMUE97Yjoxy4E",
            "company_name": "Test Company Updated",
            "website": "https://testcompany.example.com",
            "industry": "SaaS",
            "contact_name": "Alex Rivera",
            "email": "alex@testcompany.example.com",
            "phone": "+1 555-0100",
            "country": "United States",
            "monthly_budget": "9000.00",
            "goal": "Scale Pipeline",
            "services": ["Content", "AI Workflow"],
            "custom_services": "",
            "priority": "Critical",
            "deadline": "2026-09-15",
            "attachments_text": "https://example.com/spec.pdf",
            "notes": "Updated notes.",
            "status": "In Progress",
        },
        follow_redirects=True,
    )
    assert edit_resp.status_code == 200
    assert b"Test Company Updated" in edit_resp.data
    assert b"$9,000.00" in edit_resp.data

    # Quick status update
    status_resp = auth_client.post(
        f"/projects/{project_id}/status",
        data={"status": "Completed"},
        follow_redirects=True,
    )
    assert status_resp.status_code == 200
    with app.app_context():
        assert db.session.get(Project, project_id).status == "Completed"

    # Delete project
    del_resp = auth_client.post(f"/projects/{project_id}/delete", follow_redirects=True)
    assert del_resp.status_code == 200
    with app.app_context():
        assert db.session.get(Project, project_id) is None


def test_n8n_integration_trigger_and_sync(auth_client, app):
    with app.app_context():
        project = Project(
            intake_id="INT-recN8NTest00001",
            company_name="Automation Corp",
            industry="Technology",
            monthly_budget=Decimal("5000.00"),
            goal="Automate Intake",
            services=["AI Workflow"],
            priority="High",
            deadline=date(2026, 10, 1),
            status="Validated",
        )
        db.session.add(project)
        db.session.commit()
        project_id = project.id

        # Mock a successful n8n webhook response returning synchronous output
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"X-N8N-Execution-Id": "n8n-99100"}
        mock_response.json.return_value = {
            "status": "success",
            "n8n_execution_id": "n8n-99100",
            "workflow_id": "wf-intake-01",
            "workflow_name": "Project Intake Automation",
            "output": {
                "title": "Automated Intake Strategy",
                "output_type": "strategy",
                "summary": "Generated by n8n workflow",
                "content": "## Strategy Deliverable\nAll steps completed.",
                "data": {"score": 98},
                "status": "generated",
            },
        }

        with patch("app.integrations.n8n.requests.post", return_value=mock_response) as mocked_post:
            result = trigger_workflow(project, trigger_source="manual")
            assert result["ok"] is True
            assert mocked_post.called
            sent_json = mocked_post.call_args.kwargs["json"]
            assert sent_json["project_id"] == project_id
            assert sent_json["intake_id"] == "INT-recN8NTest00001"

        execution = Execution.query.filter_by(project_id=project_id).first()
        assert execution is not None
        assert execution.status == "success"
        assert execution.n8n_execution_id == "n8n-99100"

        output = Output.query.filter_by(project_id=project_id).first()
        assert output is not None
        assert output.title == "Automated Intake Strategy"
        assert output.data["score"] == 98

        # Test get_execution & sync_execution_status
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "id": "n8n-99100",
            "status": "success",
            "finished": True,
            "workflowId": "wf-intake-01",
        }
        with patch("app.integrations.n8n.requests.get", return_value=mock_get_resp):
            exec_info = get_execution("n8n-99100")
            assert exec_info["ok"] is True
            assert exec_info["status"] == "success"

            sync_res = sync_execution_status(execution)
            assert sync_res["ok"] is True

        # Test graceful handling when n8n is unreachable
        with patch(
            "app.integrations.n8n.requests.post",
            side_effect=requests.ConnectionError("Connection refused"),
        ):
            fail_result = trigger_workflow(project, trigger_source="manual")
            assert fail_result["ok"] is False
            assert fail_result["execution"].status == "failed"
            assert "Connection refused" in fail_result["execution"].error_message

    # Verify Dashboard, Executions, and Outputs UI pages render properly
    dash_resp = auth_client.get("/")
    assert dash_resp.status_code == 200
    assert b"Automation Corp" in dash_resp.data

    exec_list_resp = auth_client.get("/executions")
    assert exec_list_resp.status_code == 200
    assert b"n8n-99100" in exec_list_resp.data

    out_list_resp = auth_client.get("/outputs")
    assert out_list_resp.status_code == 200
    assert b"Automated Intake Strategy" in out_list_resp.data
