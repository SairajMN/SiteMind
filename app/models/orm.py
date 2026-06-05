from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Site(Base, TimestampMixin):
    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = _uuid_pk()
    root_url: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(Text, nullable=False)
    scope_policy: Mapped[str] = mapped_column(String(64), nullable=False, default="same_domain")

    crawl_jobs: Mapped[list["CrawlJob"]] = relationship(back_populates="site")
    pages: Mapped[list["Page"]] = relationship(back_populates="site")


class CrawlJob(Base, TimestampMixin):
    __tablename__ = "crawl_jobs"
    __table_args__ = (Index("ix_crawl_jobs_site_status", "site_id", "status"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    goal: Mapped[str | None] = mapped_column(Text)
    requested_depth: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    page_budget: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_summary: Mapped[str | None] = mapped_column(Text)

    site: Mapped["Site"] = relationship(back_populates="crawl_jobs")
    pages: Mapped[list["Page"]] = relationship(back_populates="crawl_job")
    dag_runs: Mapped[list["DagRun"]] = relationship(back_populates="crawl_job")


class Page(Base, TimestampMixin):
    __tablename__ = "pages"
    __table_args__ = (
        UniqueConstraint("crawl_job_id", "url", name="uq_pages_job_url"),
        Index("ix_pages_site_job", "site_id", "crawl_job_id"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    crawl_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE")
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    path: Mapped[str | None] = mapped_column(Text)
    status_code: Mapped[int | None] = mapped_column(Integer)
    content_hash: Mapped[str | None] = mapped_column(String(128))
    has_form: Mapped[bool] = mapped_column(Boolean, default=False)
    has_auth_hint: Mapped[bool] = mapped_column(Boolean, default=False)

    site: Mapped["Site"] = relationship(back_populates="pages")
    crawl_job: Mapped["CrawlJob"] = relationship(back_populates="pages")
    forms: Mapped[list["Form"]] = relationship(back_populates="page")
    endpoints: Mapped[list["Endpoint"]] = relationship(back_populates="page")
    auth_signals: Mapped[list["AuthSignal"]] = relationship(back_populates="page")
    assets: Mapped[list["PageAsset"]] = relationship(back_populates="page")


class PageAsset(Base, TimestampMixin):
    __tablename__ = "page_assets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_url: Mapped[str | None] = mapped_column(Text)
    local_path: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)

    page: Mapped["Page"] = relationship(back_populates="assets")


class Form(Base, TimestampMixin):
    __tablename__ = "forms"

    id: Mapped[uuid.UUID] = _uuid_pk()
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    form_index: Mapped[int] = mapped_column(Integer, default=0)
    action_url: Mapped[str | None] = mapped_column(Text)
    method: Mapped[str | None] = mapped_column(String(16))
    form_name: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    page: Mapped["Page"] = relationship(back_populates="forms")
    fields: Mapped[list["FormField"]] = relationship(back_populates="form")


class FormField(Base, TimestampMixin):
    __tablename__ = "form_fields"

    id: Mapped[uuid.UUID] = _uuid_pk()
    form_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("forms.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(Text)
    field_type: Mapped[str | None] = mapped_column(String(64))
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    placeholder: Mapped[str | None] = mapped_column(Text)
    validation_hint: Mapped[str | None] = mapped_column(Text)

    form: Mapped["Form"] = relationship(back_populates="fields")


class Endpoint(Base, TimestampMixin):
    __tablename__ = "endpoints"

    id: Mapped[uuid.UUID] = _uuid_pk()
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    request_url: Mapped[str] = mapped_column(Text, nullable=False)
    method: Mapped[str | None] = mapped_column(String(16))
    request_type: Mapped[str | None] = mapped_column(String(32))
    status_code: Mapped[int | None] = mapped_column(Integer)
    headers_json: Mapped[dict | None] = mapped_column(JSONB)
    payload_schema_json: Mapped[dict | None] = mapped_column(JSONB)
    observation_type: Mapped[str | None] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float)

    page: Mapped["Page"] = relationship(back_populates="endpoints")


class AuthSignal(Base, TimestampMixin):
    __tablename__ = "auth_signals"

    id: Mapped[uuid.UUID] = _uuid_pk()
    page_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pages.id", ondelete="CASCADE"))
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    signal_value: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    page: Mapped["Page"] = relationship(back_populates="auth_signals")


class Workflow(Base, TimestampMixin):
    __tablename__ = "workflows"

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    name: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    steps: Mapped[list["WorkflowStep"]] = relationship(back_populates="workflow")


class WorkflowStep(Base, TimestampMixin):
    __tablename__ = "workflow_steps"

    id: Mapped[uuid.UUID] = _uuid_pk()
    workflow_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workflows.id", ondelete="CASCADE")
    )
    step_index: Mapped[int] = mapped_column(Integer, default=0)
    page_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    action_type: Mapped[str | None] = mapped_column(String(64))
    selector: Mapped[str | None] = mapped_column(Text)
    endpoint_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("endpoints.id", ondelete="SET NULL")
    )
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)

    workflow: Mapped["Workflow"] = relationship(back_populates="steps")


class RetrievalChunk(Base, TimestampMixin):
    __tablename__ = "retrieval_chunks"
    __table_args__ = (
        UniqueConstraint("site_id", "chunk_hash", name="uq_chunks_site_hash"),
        Index("ix_chunks_site_artifact", "site_id", "artifact_type"),
    )

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    page_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    chunk_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    source_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    tags_json: Mapped[dict | None] = mapped_column(JSONB)

    embedding: Mapped["EmbeddingsMetadata | None"] = relationship(back_populates="chunk")


class EmbeddingsMetadata(Base, TimestampMixin):
    __tablename__ = "embeddings_metadata"

    id: Mapped[uuid.UUID] = _uuid_pk()
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("retrieval_chunks.id", ondelete="CASCADE"), unique=True
    )
    collection_name: Mapped[str] = mapped_column(String(128), nullable=False)
    vector_id: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    embedding_dim: Mapped[int | None] = mapped_column(Integer)

    chunk: Mapped["RetrievalChunk"] = relationship(back_populates="embedding")


class Answer(Base, TimestampMixin):
    __tablename__ = "answers"

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    critic_status: Mapped[str | None] = mapped_column(String(32))

    citations: Mapped[list["Citation"]] = relationship(back_populates="answer")
    critic_events: Mapped[list["CriticEvent"]] = relationship(back_populates="answer")


class Citation(Base, TimestampMixin):
    __tablename__ = "citations"
    __table_args__ = (Index("ix_citations_answer", "answer_id"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"))
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("retrieval_chunks.id", ondelete="SET NULL")
    )
    page_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    source_url: Mapped[str | None] = mapped_column(Text)
    artifact_type: Mapped[str | None] = mapped_column(String(64))
    snippet: Mapped[str | None] = mapped_column(Text)
    score: Mapped[float | None] = mapped_column(Float)

    answer: Mapped["Answer"] = relationship(back_populates="citations")


class CriticEvent(Base, TimestampMixin):
    __tablename__ = "critic_events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    answer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("answers.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text)
    recovery_action: Mapped[str | None] = mapped_column(Text)

    answer: Mapped["Answer"] = relationship(back_populates="critic_events")


class DagRun(Base, TimestampMixin):
    __tablename__ = "dag_runs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    crawl_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="CASCADE")
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    planner_version: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    crawl_job: Mapped["CrawlJob"] = relationship(back_populates="dag_runs")
    nodes: Mapped[list["DagNode"]] = relationship(back_populates="dag_run")
    edges: Mapped[list["DagEdge"]] = relationship(back_populates="dag_run")


class DagNode(Base, TimestampMixin):
    __tablename__ = "dag_nodes"
    __table_args__ = (Index("ix_dag_nodes_run_status", "dag_run_id", "status"),)

    id: Mapped[uuid.UUID] = _uuid_pk()
    dag_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dag_runs.id", ondelete="CASCADE")
    )
    node_key: Mapped[str] = mapped_column(String(128), nullable=False)
    node_type: Mapped[str | None] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    lane: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_json: Mapped[dict | None] = mapped_column(JSONB)
    output_json: Mapped[dict | None] = mapped_column(JSONB)

    dag_run: Mapped["DagRun"] = relationship(back_populates="nodes")


class DagEdge(Base, TimestampMixin):
    __tablename__ = "dag_edges"

    id: Mapped[uuid.UUID] = _uuid_pk()
    dag_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("dag_runs.id", ondelete="CASCADE")
    )
    from_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dag_nodes.id", ondelete="CASCADE"))
    to_node_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("dag_nodes.id", ondelete="CASCADE"))
    edge_type: Mapped[str | None] = mapped_column(String(64))

    dag_run: Mapped["DagRun"] = relationship(back_populates="edges")


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    crawl_job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crawl_jobs.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(32), default="pending")

    metrics: Mapped[list["EvaluationMetric"]] = relationship(back_populates="evaluation")


class EvaluationMetric(Base, TimestampMixin):
    __tablename__ = "evaluation_metrics"

    id: Mapped[uuid.UUID] = _uuid_pk()
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE")
    )
    metric_key: Mapped[str] = mapped_column(String(128), nullable=False)
    metric_value: Mapped[float | None] = mapped_column(Float)
    details_json: Mapped[dict | None] = mapped_column(JSONB)

    evaluation: Mapped["Evaluation"] = relationship(back_populates="metrics")


class GeneratedApi(Base, TimestampMixin):
    __tablename__ = "generated_apis"

    id: Mapped[uuid.UUID] = _uuid_pk()
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workflows.id", ondelete="SET NULL")
    )
    site_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sites.id", ondelete="CASCADE"))
    spec_json: Mapped[dict | None] = mapped_column(JSONB)
    openapi_url: Mapped[str | None] = mapped_column(Text)
