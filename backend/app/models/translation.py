import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime, Text, func


class Translation(SQLModel, table=True):
    __tablename__ = "translations"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    source_text: str = Field(sa_type=Text, nullable=False)
    source_lang: str = Field(max_length=10, nullable=False)
    target_lang: str = Field(max_length=10, nullable=False)
    translated_text: Optional[str] = Field(sa_type=Text, default=None)
    model_used: Optional[str] = Field(max_length=50, default=None)
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    cost: Optional[float] = None
    status: str = Field(max_length=20, default="success", nullable=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    )
