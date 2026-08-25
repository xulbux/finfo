import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)
