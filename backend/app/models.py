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
    TEAM = "team"


class Segment(BaseModel):
    id: UUID
    type: SegmentType
    sort_order: int
    title: str
    content: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)
    page_id: str | None = None
    created_at: datetime
    updated_at: datetime


class SegmentCreateRequest(BaseModel):
    type: SegmentType
    title: str = ""
    page_id: str | None = None
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
    page_id: str | None = None
    created_at: datetime
    updated_at: datetime


class SiteResponse(BaseModel):
    title: str


class Page(BaseModel):
    id: str
    name: str
    slug: str
    sort_order: int
    is_system: bool = False
    is_hidden: bool = False
    created_at: datetime
    updated_at: datetime


class PageCreateRequest(BaseModel):
    name: str
    slug: str


class PageUpdateRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_hidden: bool | None = None


class PageReorderRequest(BaseModel):
    page_ids: list[str]


class TeamMember(BaseModel):
    id: str
    name: str
    student_number: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class TeamMemberCreateRequest(BaseModel):
    name: str
    student_number: str


class TeamMemberReorderRequest(BaseModel):
    member_ids: list[str]
