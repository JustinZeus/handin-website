from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class SegmentType(StrEnum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    VIDEO = "video"
    AUDIO = "audio"
    IFRAME = "iframe"
    GALLERY = "gallery"
    LINK = "link"


class Segment(BaseModel):
    id: UUID
    type: SegmentType
    sort_order: int
    title: str
    content: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class SegmentCreateRequest(BaseModel):
    type: SegmentType
    title: str
    content: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class SegmentUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    metadata: dict[str, object] | None = None


class ReorderRequest(BaseModel):
    segment_ids: list[UUID]


class SiteUpdateRequest(BaseModel):
    title: str


class SegmentResponse(BaseModel):
    id: UUID
    type: SegmentType
    sort_order: int
    title: str
    content: str
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class SiteResponse(BaseModel):
    title: str
