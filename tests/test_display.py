from datetime import datetime
from typing import Any
from helpers.display import display_info, format_relative_time
import pytest


class TestDisplay:
    """
    **LB1:** Unit Test – Display rendering<br>
    **Topics:** Output Rendering, Relative Time Formatting
    """

    def test_format_relative_time_default_now(self) -> None:
        """
        **Topic:** Relative Time Formatting<br>
        **Focus:** Testing time formatting with default reference.\n
        ----------------------------------------------------------------------------------------------------
        Tests `format_relative_time` when `reference_time` is omitted (defaults to now).
        """

        now = datetime.now()
        result = format_relative_time(now)
        assert result is not None
        assert "today" in result

    def test_display_info_flat_and_nested(self, capsys: pytest.CaptureFixture[str]) -> None:
        """
        **Topic:** Output Rendering<br>
        **Focus:** Testing formatted output of nested structures.\n
        ----------------------------------------------------------------------------------------------------
        Tests `display_info` prints formatted output including nested dicts, datetimes, and ignores `None`.
        """

        sample_data: dict[str, Any] = {
            "name": "test.txt",
            "size": 1024,
            "created_at": datetime(2026, 8, 18, 10, 0, 0),
            "skipped_none": None,
            "hashes": {
                "md5": "d41d8cd98f00b204e9800998ecf8427e",
                "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            },
        }

        display_info(sample_data, title="File Information")
        captured = capsys.readouterr().out

        assert "--- FILE INFORMATION ---" in captured
        assert "Name: test.txt" in captured
        assert "Size: 1024" in captured
        assert "Created At:" in captured
        assert "Skipped None" not in captured
        assert "Hashes:" in captured
        assert "  Md5: d41d8cd98f00b204e9800998ecf8427e" in captured
