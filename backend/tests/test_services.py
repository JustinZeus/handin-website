import time
from pathlib import Path
from uuid import uuid4

import pytest

from app.models import SegmentCreateRequest, SegmentType, SegmentUpdateRequest
from app.services.segment_service import (
    create_segment,
    delete_segment,
    get_segment,
    list_segments,
    reorder_segments,
    update_segment,
)
from app.services.site_service import get_site_title, update_site_title

# --- Segment Service Tests ---


def test_create_segment(db: Path) -> None:
    request = SegmentCreateRequest(
        type=SegmentType.MARKDOWN,
        title="Intro",
        content="Hello world",
    )
    segment = create_segment(db, request)

    assert segment.id is not None
    assert segment.sort_order == 0
    assert segment.title == "Intro"
    assert segment.type == SegmentType.MARKDOWN
    assert segment.content == "Hello world"
    assert segment.created_at == segment.updated_at


def test_create_segment_auto_increments_sort_order(db: Path) -> None:
    for i in range(3):
        request = SegmentCreateRequest(
            type=SegmentType.MARKDOWN,
            title=f"Segment {i}",
        )
        segment = create_segment(db, request)
        assert segment.sort_order == i


def test_list_segments_empty(db: Path) -> None:
    segments = list_segments(db)
    assert segments == []


def test_list_segments_ordered(db: Path) -> None:
    titles = ["First", "Second", "Third"]
    for title in titles:
        create_segment(
            db,
            SegmentCreateRequest(type=SegmentType.MARKDOWN, title=title),
        )

    segments = list_segments(db)
    assert [s.title for s in segments] == titles
    assert [s.sort_order for s in segments] == [0, 1, 2]


def test_get_segment_found(db: Path) -> None:
    created = create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.PDF, title="Slides"),
    )
    fetched = get_segment(db, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.title == "Slides"
    assert fetched.type == SegmentType.PDF


def test_get_segment_not_found(db: Path) -> None:
    result = get_segment(db, uuid4())
    assert result is None


def test_update_segment_title(db: Path) -> None:
    created = create_segment(
        db,
        SegmentCreateRequest(
            type=SegmentType.MARKDOWN,
            title="Old Title",
            content="Keep me",
        ),
    )
    time.sleep(0.01)
    updated = update_segment(
        db,
        created.id,
        SegmentUpdateRequest(title="New Title"),
    )

    assert updated is not None
    assert updated.title == "New Title"
    assert updated.content == "Keep me"
    assert updated.updated_at > updated.created_at


def test_update_segment_not_found(db: Path) -> None:
    result = update_segment(
        db,
        uuid4(),
        SegmentUpdateRequest(title="Nope"),
    )
    assert result is None


def test_delete_segment(db: Path) -> None:
    created = create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.MARKDOWN, title="Bye"),
    )
    assert delete_segment(db, created.id) is True
    assert get_segment(db, created.id) is None


def test_delete_segment_not_found(db: Path) -> None:
    assert delete_segment(db, uuid4()) is False


def test_reorder_segments(db: Path) -> None:
    a = create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.MARKDOWN, title="A"),
    )
    b = create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.MARKDOWN, title="B"),
    )
    c = create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.MARKDOWN, title="C"),
    )

    reorder_segments(db, [c.id, a.id, b.id])
    segments = list_segments(db)

    assert [s.title for s in segments] == ["C", "A", "B"]
    assert [s.sort_order for s in segments] == [0, 1, 2]


def test_reorder_segments_invalid_ids(db: Path) -> None:
    create_segment(
        db,
        SegmentCreateRequest(type=SegmentType.MARKDOWN, title="Only"),
    )
    with pytest.raises(ValueError):
        reorder_segments(db, [uuid4()])


# --- Site Service Tests ---


def test_get_site_title_default(db: Path) -> None:
    assert get_site_title(db) == "Untitled Site"


def test_update_and_get_site_title(db: Path) -> None:
    update_site_title(db, "My Course")
    assert get_site_title(db) == "My Course"


def test_update_site_title_overwrites(db: Path) -> None:
    update_site_title(db, "First")
    update_site_title(db, "Second")
    assert get_site_title(db) == "Second"
