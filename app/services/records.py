from typing import TypeVar
from uuid import UUID

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Base

Record = TypeVar("Record", bound=Base)


async def require_record(session: AsyncSession, model: type[Record], record_id: UUID) -> Record:
    record = await session.get(model, record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return record


async def create_record(session: AsyncSession, model: type[Record], data: BaseModel, **extra) -> Record:
    record = model(**data.model_dump(), **extra)
    session.add(record)
    await session.flush()
    await session.refresh(record)
    return record


async def update_record(session: AsyncSession, record: Record, data: BaseModel) -> Record:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    await session.flush()
    await session.refresh(record)
    return record
