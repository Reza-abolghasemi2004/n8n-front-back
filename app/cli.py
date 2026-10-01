from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import os
import click
from flask import Flask
from app.extensions import db
from app.models.execution import Execution
from app.models.output import Output
from app.models.project import Project
from app.models.user import AdminUser


def register_cli_commands(app: Flask) -> None:
    @app.cli.command("create-admin")
    @click.option("--username", default=lambda: os.getenv("ADMIN_USERNAME", "admin"), help="Admin username")
    @click.option("--email", default=lambda: os.getenv("ADMIN_EMAIL", "admin@example.com"), help="Admin email")
    @click.option(
        "--password",
        default=lambda: os.getenv("ADMIN_PASSWORD", ""),
        help="Admin password (prompts if omitted)",
    )
    @click.option("--full-name", default="Platform Administrator", help="Display name")
    def create_admin(username: str, email: str, password: str, full_name: str) -> None:
        """Create or update the Administrator user account."""
        if not password or password == "CHANGE_ME":
            password = click.prompt("Enter admin password", hide_input=True, confirmation_prompt=True)

        user = AdminUser.query.filter(
            (AdminUser.username == username) | (AdminUser.email == email)
        ).first()

        if user:
            user.username = username
            user.email = email
            user.full_name = full_name
            user.set_password(password)
            user.is_active_user = True
            db.session.commit()
            click.echo(f"Updated existing admin account: {username} ({email})")
        else:
            user = AdminUser(
                username=username,
                email=email,
                full_name=full_name,
                is_active_user=True,
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            click.echo(f"Created admin account: {username} ({email})")

    @app.cli.command("seed-demo")
    def seed_demo() -> None:
        """Seed realistic sample projects, n8n executions, and outputs for demonstration."""
        now = datetime.now(timezone.utc)
        today = date.today()

        sample_projects = [
            {
                "intake_id": "INT-recgWMUE97Yjoxy4E",
                "company_name": "Apex Cloud Systems",
                "website": "https://apexcloud.io",
                "industry": "Technology",
                "contact_name": "Elena Vance",
                "email": "elena.vance@apexcloud.io",
                "phone": "+1 (415) 890-4312",
                "country": "United States",
                "monthly_budget": Decimal("12500.00"),
                "goal": "Generate Qualified Enterprise Leads",
                "services": ["Content", "Lead Generation", "AI Workflow", "SEO"],
                "priority": "High",
                "deadline": today + timedelta(days=21),
                "attachments": [
                    {
                        "name": "Q4_Growth_Brief.pdf",
                        "url": "https://assets.apexcloud.io/docs/q4-growth-brief.pdf",
                        "type": "pdf",
                    },
                    {
                        "name": "ICP_Persona_Matrix.xlsx",
                        "url": "https://assets.apexcloud.io/docs/icp-matrix.xlsx",
                        "type": "spreadsheet",
                    },
                ],
                "notes": "Enterprise B2B SaaS intake. Priority focus on automated outbound enrichment via n8n and technical content pipeline.",
                "status": "Validated",
                "created_at": now - timedelta(days=5, hours=3),
            },
            {
                "intake_id": "INT-rec9KpL2mXq8VzN1B",
                "company_name": "Nordic FinPay AB",
                "website": "https://nordicfinpay.se",
                "industry": "FinTech",
                "contact_name": "Henrik Lindqvist",
                "email": "h.lindqvist@nordicfinpay.se",
                "phone": "+46 8 501 234 90",
                "country": "Sweden",
                "monthly_budget": Decimal("18000.00"),
                "goal": "Cross-Border Merchant Onboarding Automation",
                "services": ["AI Workflow", "CRM Integration", "Email Automation"],
                "priority": "Critical",
                "deadline": today + timedelta(days=10),
                "attachments": [
                    {
                        "name": "KYB_Workflow_Spec_v2.pdf",
                        "url": "https://nordicfinpay.se/specs/kyb-v2.pdf",
                        "type": "pdf",
                    }
                ],
                "notes": "Requires automated KYB document extraction and HubSpot pipeline sync through n8n.",
                "status": "In Progress",
                "created_at": now - timedelta(days=4, hours=6),
            },
            {
                "intake_id": "INT-rec4TrW7pBn3YcJ8Q",
                "company_name": "Verde Botanicals Co.",
                "website": "https://verdebio.com",
                "industry": "E-Commerce",
                "contact_name": "Sofia Morales",
                "email": "sofia@verdebio.com",
                "phone": "+1 (512) 442-9811",
                "country": "United States",
                "monthly_budget": Decimal("6400.00"),
                "goal": "Increase Repeat Purchase Rate & Organic Traffic",
                "services": ["Content", "SEO", "Email Automation", "Social Media"],
                "priority": "Medium",
                "deadline": today + timedelta(days=30),
                "attachments": [
                    {
                        "name": "Brand_Style_Guide_2026.pdf",
                        "url": "https://verdebio.com/brand-guide.pdf",
                        "type": "pdf",
                    }
                ],
                "notes": "DTC skincare brand seeking automated klaviyo flow copy generation and SEO topic cluster plans.",
                "status": "Completed",
                "created_at": now - timedelta(days=7, hours=2),
            },
            {
                "intake_id": "INT-rec7HnD5vGf2MwA6K",
                "company_name": "Helios MedTech GmbH",
                "website": "https://helios-medtech.de",
                "industry": "Healthcare",
                "contact_name": "Dr. Lukas Weber",
                "email": "l.weber@helios-medtech.de",
                "phone": "+49 30 901820",
                "country": "Germany",
                "monthly_budget": Decimal("22000.00"),
                "goal": "Clinical Partner Portal & Lead Qualification",
                "services": ["Lead Generation", "CRM Integration", "Web Analytics"],
                "priority": "High",
                "deadline": today + timedelta(days=14),
                "attachments": [],
                "notes": "Strict GDPR compliance required. n8n instance processes EU clinic inquiries directly into PostgreSQL.",
                "status": "Queued",
                "created_at": now - timedelta(days=2, hours=9),
            },
            {
                "intake_id": "INT-rec2ZxC8bNm4QwP9L",
                "company_name": "Stratos Logistics Group",
                "website": "https://stratosfreight.ca",
                "industry": "Logistics",
                "contact_name": "Marcus Chen",
                "email": "mchen@stratosfreight.ca",
                "phone": "+1 (604) 719-2045",
                "country": "Canada",
                "monthly_budget": Decimal("9500.00"),
                "goal": "Automated RFP Triage & Quote Preparation",
                "services": ["AI Workflow", "CRM Integration"],
                "priority": "High",
                "deadline": today + timedelta(days=7),
                "attachments": [
                    {
                        "name": "Sample_RFP_Dataset.json",
                        "url": "https://stratosfreight.ca/rfp-sample.json",
                        "type": "json",
                    }
                ],
                "notes": "Webhook timeout occurred on legacy ERP endpoint; credentials being rotated by client IT.",
                "status": "Failed",
                "created_at": now - timedelta(days=3, hours=1),
            },
            {
                "intake_id": "INT-rec6JmP1kRt9SvE3W",
                "company_name": "Luminary EdTech Labs",
                "website": "https://luminarylearn.org",
                "industry": "Education",
                "contact_name": "Priya Nair",
                "email": "priya@luminarylearn.org",
                "phone": "+44 20 7946 0921",
                "country": "United Kingdom",
                "monthly_budget": Decimal("4800.00"),
                "goal": "Paid Acquisition & Content Funnel",
                "services": ["Paid Ads", "Content", "Web Analytics"],
                "priority": "Low",
                "deadline": today + timedelta(days=45),
                "attachments": [],
                "notes": "New intake awaiting initial validation before triggering n8n discovery workflow.",
                "status": "New",
                "created_at": now - timedelta(hours=14),
            },
        ]

        created_projects = {}
        for p_data in sample_projects:
            existing = Project.query.filter_by(intake_id=p_data["intake_id"]).first()
            if not existing:
                proj = Project(**p_data)
                db.session.add(proj)
                db.session.flush()
                created_projects[p_data["intake_id"]] = proj
            else:
                created_projects[p_data["intake_id"]] = existing

        if Execution.query.count() == 0:
            p1 = created_projects["INT-recgWMUE97Yjoxy4E"]
            p2 = created_projects["INT-rec9KpL2mXq8VzN1B"]
            p3 = created_projects["INT-rec4TrW7pBn3YcJ8Q"]
            p4 = created_projects["INT-rec7HnD5vGf2MwA6K"]
            p5 = created_projects["INT-rec2ZxC8bNm4QwA6K" if "INT-rec2ZxC8bNm4QwA6K" in created_projects else "INT-rec2ZxC8bNm4QwP9L"]

            exec1 = Execution(
                project_id=p1.id,
                n8n_execution_id="n8n-exec-88412",
                workflow_id="wf-intake-validator-01",
                workflow_name="Project Intake Validation & Enrichment",
                trigger_source="webhook",
                status="success",
                payload=p1.to_n8n_payload(),
                response_data={
                    "execution_id": "n8n-exec-88412",
                    "status": "success",
                    "enriched_domain": "apexcloud.io",
                    "company_size": "250-500",
                    "tech_stack": ["Kubernetes", "PostgreSQL", "HubSpot", "Segment"],
                    "validation_score": 96,
                },
                started_at=now - timedelta(days=4, hours=2),
                finished_at=now - timedelta(days=4, hours=1, minutes=58),
            )
            exec2 = Execution(
                project_id=p2.id,
                n8n_execution_id="n8n-exec-88459",
                workflow_id="wf-kyb-automation-02",
                workflow_name="Merchant Onboarding & CRM Pipeline Sync",
                trigger_source="manual",
                status="running",
                payload=p2.to_n8n_payload(),
                response_data={
                    "execution_id": "n8n-exec-88459",
                    "status": "running",
                    "current_node": "PostgreSQL Output Writer",
                    "progress_pct": 75,
                },
                started_at=now - timedelta(minutes=8),
                finished_at=None,
            )
            exec3 = Execution(
                project_id=p3.id,
                n8n_execution_id="n8n-exec-88390",
                workflow_id="wf-content-seo-03",
                workflow_name="Content & SEO Strategy Generator",
                trigger_source="webhook",
                status="success",
                payload=p3.to_n8n_payload(),
                response_data={
                    "execution_id": "n8n-exec-88390",
                    "status": "success",
                    "clusters_generated": 6,
                    "emails_drafted": 5,
                    "tokens_used": 14820,
                },
                started_at=now - timedelta(days=6, hours=5),
                finished_at=now - timedelta(days=6, hours=4, minutes=57),
            )
            exec4 = Execution(
                project_id=p5.id,
                n8n_execution_id="n8n-exec-88431",
                workflow_id="wf-rfp-triage-04",
                workflow_name="RFP Document Extraction & Quote Engine",
                trigger_source="manual",
                status="failed",
                error_message="Node 'ERP Rate Lookup' returned HTTP 502 Bad Gateway after 3 retries.",
                payload=p5.to_n8n_payload(),
                response_data={
                    "execution_id": "n8n-exec-88431",
                    "status": "failed",
                    "failed_node": "ERP Rate Lookup",
                    "http_status": 502,
                },
                started_at=now - timedelta(days=2, hours=4),
                finished_at=now - timedelta(days=2, hours=3, minutes=59),
            )
            exec5 = Execution(
                project_id=p4.id,
                n8n_execution_id="n8n-exec-88463",
                workflow_id="wf-intake-validator-01",
                workflow_name="Project Intake Validation & Enrichment",
                trigger_source="status_change",
                status="success",
                payload=p4.to_n8n_payload(),
                response_data={
                    "execution_id": "n8n-exec-88463",
                    "status": "success",
                    "gdpr_check": "passed",
                    "region_routing": "eu-central-1",
                },
                started_at=now - timedelta(days=1, hours=12),
                finished_at=now - timedelta(days=1, hours=11, minutes=59),
            )

            db.session.add_all([exec1, exec2, exec3, exec4, exec5])
            db.session.flush()

            out1 = Output(
                project_id=p1.id,
                execution_id=exec1.id,
                title="Enterprise Account Enrichment & Outbound Playbook",
                output_type="strategy",
                status="approved",
                summary="Validated ICP enrichment report covering 150 high-intent cloud infrastructure accounts with multi-channel sequences.",
                content=(
                    "## Executive Summary\n"
                    "n8n completed automated domain enrichment and technographic scoring for **Apex Cloud Systems**.\n\n"
                    "### Key Findings\n"
                    "- **Validation Score:** 96/100\n"
                    "- **Target Segment:** Mid-to-Enterprise DevOps & Platform Engineering teams (250–500 employees)\n"
                    "- **Primary Value Hook:** Automated Kubernetes cost & compliance telemetry\n\n"
                    "### Recommended Workflow Actions\n"
                    "1. Sync enriched buying committee contacts to HubSpot sequence `ENT-Q4-CLOUD`.\n"
                    "2. Publish 4 technical pillar articles targeting high-intent migration keywords.\n"
                    "3. Trigger LinkedIn intent webhook on pricing page visits."
                ),
                data={
                    "validation_score": 96,
                    "qualified_accounts": 150,
                    "primary_channels": ["LinkedIn", "Technical Content", "Outbound Email"],
                    "estimated_pipeline_value_usd": 420000,
                },
                created_at=now - timedelta(days=4, hours=1, minutes=55),
            )
            out2 = Output(
                project_id=p3.id,
                execution_id=exec3.id,
                title="Organic Topic Cluster Architecture & Retention Flows",
                output_type="content",
                status="approved",
                summary="Complete 90-day editorial roadmap and 5-part post-purchase email automation generated by n8n.",
                content=(
                    "## Deliverable Overview\n"
                    "Generated for **Verde Botanicals Co.** (`INT-rec4TrW7pBn3YcJ8Q`).\n\n"
                    "### SEO Topic Clusters\n"
                    "- **Cluster 1:** Botanical Barrier Repair (14,200 monthly searches)\n"
                    "- **Cluster 2:** Clean Formulation Ingredient Transparency (9,800 monthly searches)\n"
                    "- **Cluster 3:** Seasonal Hydration Routines (18,500 monthly searches)\n\n"
                    "### Automated Retention Sequence\n"
                    "- Day 0: Formulation usage guide\n"
                    "- Day 7: Skin check-in + routine tip\n"
                    "- Day 21: Replenishment reminder with 1-click reorder link"
                ),
                data={
                    "topic_clusters": 6,
                    "target_keywords": 48,
                    "email_templates_ready": 5,
                    "projected_organic_lift_pct": 38.5,
                },
                created_at=now - timedelta(days=6, hours=4, minutes=55),
            )
            out3 = Output(
                project_id=p4.id,
                execution_id=exec5.id,
                title="EU Clinical Partner Compliance & Lead Routing Matrix",
                output_type="report",
                status="generated",
                summary="Automated GDPR data residency verification and DACH region clinic scoring matrix.",
                content=(
                    "## DACH Clinical Partner Qualification\n"
                    "n8n verified data residency rules and scored 64 regional diagnostic centers in Germany, Austria, and Switzerland.\n\n"
                    "- **Tier 1 Clinics:** 22\n"
                    "- **Tier 2 Clinics:** 42\n"
                    "- **CRM Routing:** Assigned to DACH Enterprise Pod"
                ),
                data={
                    "gdpr_verified": True,
                    "tier_1_clinics": 22,
                    "tier_2_clinics": 42,
                    "region": "DACH",
                },
                created_at=now - timedelta(days=1, hours=11, minutes=58),
            )

            db.session.add_all([out1, out2, out3])

        db.session.commit()
        click.echo("Demo data seeded into PostgreSQL.")
