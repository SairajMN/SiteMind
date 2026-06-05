"""Q&A API routes — ask grounded questions about a site."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.orm import Answer, Citation, CriticEvent
from app.schemas.common import ApiResponse
from app.schemas.qa import AnswerResponse, AskRequest, CitationSchema
from app.services.answer_service import generate_answer
from app.services.critic_service import verify_answer
from app.services.retrieval_service import retrieve_evidence

router = APIRouter(prefix="/sites/{site_id}/ask", tags=["qa"])


@router.post("")
async def ask_question(
    site_id: uuid.UUID,
    body: AskRequest,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[AnswerResponse]:
    evidence = await retrieve_evidence(
        body.question,
        site_id=str(site_id),
        artifact_types=body.artifact_types,
        top_k=10,
    )

    result = await generate_answer(session, site_id, body.question, evidence)

    answer_text = result.get("answer", "I could not generate an answer.")
    confidence = result.get("confidence", 0.0)
    citation_urls = result.get("citations", [])

    answer_row = Answer(
        site_id=site_id,
        question=body.question,
        answer_text=answer_text,
        confidence=confidence,
        critic_status="pending",
    )
    session.add(answer_row)
    await session.flush()

    citation_models = []
    for cit in citation_urls:
        matching = [e for e in evidence if e.get("source_url") == cit]
        snippet = matching[0].get("snippet", "") if matching else ""
        artifact_type = matching[0].get("artifact_type", "page") if matching else "page"
        score = matching[0].get("score", 0.0) if matching else 0.0
        citation_row = Citation(
            answer_id=answer_row.id,
            source_url=cit,
            artifact_type=artifact_type,
            snippet=snippet,
            score=score,
        )
        session.add(citation_row)
        citation_models.append(
            CitationSchema(
                source_url=cit,
                artifact_type=artifact_type,
                snippet=snippet[:200],
                score=score,
                confidence=confidence,
            )
        )

    # Run critic verification
    critic_result = await verify_answer(body.question, answer_text, evidence)
    critic_status = critic_result.get("status", "passed")
    answer_row.critic_status = critic_status

    critic_event = CriticEvent(
        answer_id=answer_row.id,
        status=critic_status,
        reason="; ".join(critic_result.get("reasons", [])),
        recovery_action=critic_result.get("recovery_action"),
    )
    session.add(critic_event)
    await session.flush()

    return ApiResponse.ok(
        AnswerResponse(
            answer_id=answer_row.id,
            site_id=site_id,
            question=body.question,
            answer_text=answer_text,
            confidence=confidence,
            critic_status=critic_status,
            citations=citation_models,
            created_at=answer_row.created_at,
        )
    )