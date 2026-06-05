"""initial schema

Revision ID: 194bb949ae2c
Revises:
Create Date: 2026-06-04 23:33:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "194bb949ae2c"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("root_url", sa.Text(), nullable=False),
        sa.Column("domain", sa.Text(), nullable=False),
        sa.Column("scope_policy", sa.String(64), nullable=False, server_default="same_domain"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "crawl_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("requested_depth", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("page_budget", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_crawl_jobs_site_status", "crawl_jobs", ["site_id", "status"])

    op.create_table(
        "pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crawl_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("depth", sa.Integer(), server_default="0"),
        sa.Column("path", sa.Text(), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(128), nullable=True),
        sa.Column("has_form", sa.Boolean(), server_default="false"),
        sa.Column("has_auth_hint", sa.Boolean(), server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("crawl_job_id", "url", name="uq_pages_job_url"),
    )
    op.create_index("ix_pages_site_job", "pages", ["site_id", "crawl_job_id"])

    op.create_table(
        "page_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("asset_type", sa.String(64), nullable=False),
        sa.Column("asset_url", sa.Text(), nullable=True),
        sa.Column("local_path", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "forms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("form_index", sa.Integer(), server_default="0"),
        sa.Column("action_url", sa.Text(), nullable=True),
        sa.Column("method", sa.String(16), nullable=True),
        sa.Column("form_name", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "form_fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("form_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("forms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("label", sa.Text(), nullable=True),
        sa.Column("field_type", sa.String(64), nullable=True),
        sa.Column("required", sa.Boolean(), server_default="false"),
        sa.Column("placeholder", sa.Text(), nullable=True),
        sa.Column("validation_hint", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_url", sa.Text(), nullable=False),
        sa.Column("method", sa.String(16), nullable=True),
        sa.Column("request_type", sa.String(32), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("headers_json", postgresql.JSONB(), nullable=True),
        sa.Column("payload_schema_json", postgresql.JSONB(), nullable=True),
        sa.Column("observation_type", sa.String(32), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "auth_signals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("signal_type", sa.String(64), nullable=False),
        sa.Column("signal_value", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "retrieval_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("artifact_type", sa.String(64), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_hash", sa.String(128), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("tags_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.UniqueConstraint("site_id", "chunk_hash", name="uq_chunks_site_hash"),
    )
    op.create_index("ix_chunks_site_artifact", "retrieval_chunks", ["site_id", "artifact_type"])

    op.create_table(
        "embeddings_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("retrieval_chunks.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("collection_name", sa.String(128), nullable=False),
        sa.Column("vector_id", sa.String(128), nullable=False),
        sa.Column("embedding_model", sa.String(128), nullable=True),
        sa.Column("embedding_dim", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("critic_status", sa.String(32), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("retrieval_chunks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("artifact_type", sa.String(64), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_citations_answer", "citations", ["answer_id"])

    op.create_table(
        "critic_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("answer_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("answers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("recovery_action", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "dag_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crawl_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crawl_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("planner_version", sa.String(32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "dag_nodes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dag_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dag_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_key", sa.String(128), nullable=False),
        sa.Column("node_type", sa.String(64), nullable=True),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("attempt_count", sa.Integer(), server_default="0"),
        sa.Column("lane", sa.String(32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_json", postgresql.JSONB(), nullable=True),
        sa.Column("output_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_dag_nodes_run_status", "dag_nodes", ["dag_run_id", "status"])

    op.create_table(
        "dag_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dag_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dag_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dag_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("to_node_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("dag_nodes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("edge_type", sa.String(64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crawl_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("crawl_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(32), server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "evaluation_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("evaluation_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metric_key", sa.String(128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=True),
        sa.Column("details_json", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "generated_apis",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True),
        sa.Column("site_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("sites.id", ondelete="CASCADE"), nullable=False),
        sa.Column("spec_json", postgresql.JSONB(), nullable=True),
        sa.Column("openapi_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    op.create_table(
        "workflow_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_index", sa.Integer(), server_default="0"),
        sa.Column("page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("pages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action_type", sa.String(64), nullable=True),
        sa.Column("selector", sa.Text(), nullable=True),
        sa.Column("endpoint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("endpoints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("workflow_steps")
    op.drop_table("generated_apis")
    op.drop_table("evaluation_metrics")
    op.drop_table("evaluations")
    op.drop_table("dag_edges")
    op.drop_table("dag_nodes")
    op.drop_table("dag_runs")
    op.drop_table("critic_events")
    op.drop_table("citations")
    op.drop_table("answers")
    op.drop_table("embeddings_metadata")
    op.drop_table("retrieval_chunks")
    op.drop_table("workflows")
    op.drop_table("auth_signals")
    op.drop_table("endpoints")
    op.drop_table("form_fields")
    op.drop_table("forms")
    op.drop_table("page_assets")
    op.drop_table("pages")
    op.drop_table("crawl_jobs")
    op.drop_table("sites")