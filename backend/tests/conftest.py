import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings

TEST_ADMIN_TOKEN = "test-secret-token"


@pytest.fixture
def tmp_data_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmpdir:
        data_dir = Path(tmpdir)
        (data_dir / "assets").mkdir()
        yield data_dir


@pytest.fixture
def _env_settings(tmp_data_dir: Path) -> Generator[None, None, None]:
    original_env = os.environ.copy()
    os.environ["HANDIN_ADMIN_TOKEN"] = TEST_ADMIN_TOKEN
    os.environ["HANDIN_DATA_DIR"] = str(tmp_data_dir)

    from app.config import get_settings

    get_settings.cache_clear()
    yield
    os.environ.clear()
    os.environ.update(original_env)
    get_settings.cache_clear()


@pytest.fixture
def settings(_env_settings: None) -> Settings:
    from app.config import get_settings

    s = get_settings()
    assert isinstance(s, Settings)
    return s


@pytest.fixture
def db(tmp_data_dir: Path) -> Path:
    """Return path to an initialized SQLite database in the temp dir."""
    from app.database import init_db

    db_path = tmp_data_dir / "handin.db"
    init_db(db_path)
    return db_path


@pytest.fixture
def client(_env_settings: None) -> TestClient:
    from app.main import app

    return TestClient(app)
