"""Forms API routes."""
from __future__ import annotations
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.orm import Form, FormField
from app.schemas.common import ApiResponse
from app.schemas.form import FormFieldSummary, FormListResponse, FormSummary

router = APIRouter(prefix="/sites/{site_id}/forms", tags=["forms"])

@router.get("")
async def list_forms(
    site_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[FormListResponse]:
    from app.models.orm import Page
    result = await session.execute(
        select(Form).join(Page).where(Page.site_id == site_id)
    )
    forms = result.scalars().all()
    summaries = []
    for form in forms:
        field_result = await session.execute(
            select(FormField).where(FormField.form_id == form.id)
        )
        fields = field_result.scalars().all()
        summaries.append(
            FormSummary(
                id=form.id, page_id=form.page_id, form_index=form.form_index,
                action_url=form.action_url, method=form.method,
                form_name=form.form_name, confidence=form.confidence,
                fields=[FormFieldSummary(id=f.id, name=f.name, label=f.label, field_type=f.field_type, required=f.required, placeholder=f.placeholder) for f in fields],
                created_at=form.created_at,
            )
        )
    return ApiResponse.ok(FormListResponse(forms=summaries, total=len(summaries)))
