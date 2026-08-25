import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from helpers.display import format_relative_time
from helpers.extractors import get_owner_group
import pytest
from freezegun import freeze_time


class TestCategory2:
    """
    **LB1:** Unit Test 2 – Free Choice<br>
    **Topics:** Time-Freezing & Advanced Mocking
    """

    @freeze_time("2026-08-18 15:00:00")
    def test_time_freezing(self) -> None:
        """
        **Topic:** Time-Freezing / Clock Mocking<br>
        **Focus:** Testing time-dependent functions with a frozen clock.\n
        ----------------------------------------------------------------------------------------------------
        We freeze the time globally to `August 18, 2026 15:00`.<br>
        We call `format_relative_time` **without** an explicit `reference_time`,<br>
        so it uses `datetime.now()` internally, which was frozen by freezegun.
        """

        # Exactly 2 days before:
        file_date = datetime(2026, 8, 16, 12, 0, 0)

        # Without `reference_time`; relies on global `datetime.now()`:
        result = format_relative_time(file_date)

        assert result == "at 12:00, 2 days ago"

    def test_advanced_mocking_os_behavior(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """
        **Topic:** Advanced Mocking<br>
        **Focus:** Mocking OS behavior and external modules to test error handling.\n
        ----------------------------------------------------------------------------------------------------
        We mock the system platform and a complex Windows module (`win32security`),<br>
        to test the correct error handling and fallback behavior of `get_owner_group`,<br>
        even if we run the test on Linux.
        """

        test_file = tmp_path / "mock_test.txt"
        test_file.touch()

        # [1] We pretend that we are on Windows (`win32`):
        monkeypatch.setattr("sys.platform", "win32")

        # [2] We mock the `win32security` module completely (bc missing on Linux/Mac):
        mock_win32 = MagicMock()
        monkeypatch.setitem(sys.modules, "win32security", mock_win32)

        # [3] We simulate a working `LookupAccountSid` function.
        # It normally returns a Tuple `(name, domain, type)`:
        mock_win32.LookupAccountSid.side_effect = [
            ("JulBuy", "LAPTOP-JULBUY", 1),  # Owner
            ("Users", "BUILTIN", 2),  # Group
        ]

        owner, group = get_owner_group(test_file)

        assert owner == "LAPTOP-JULBUY\\JulBuy"
        assert group == "BUILTIN\\Users"
        assert mock_win32.GetFileSecurity.called
        assert mock_win32.LookupAccountSid.call_count == 2

    def test_mocking_posix_fallback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """
        **Topic:** Advanced Mocking (POSIX Fallback)<br>
        **Focus:** Verifying cross-platform fallback logic for Linux/macOS.\n
        ----------------------------------------------------------------------------------------------------
        We simulate a POSIX platform (linux) where `path.owner()` and `path.group()` are used.
        """

        test_file = tmp_path / "posix_test.txt"
        test_file.touch()

        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setattr(Path, "owner", lambda self: "testuser")  # pyright:ignore[reportUnknownArgumentType,reportUnknownLambdaType]
        monkeypatch.setattr(Path, "group", lambda self: "testgroup")  # pyright:ignore[reportUnknownArgumentType,reportUnknownLambdaType]

        owner, group = get_owner_group(test_file)
        assert owner == "testuser"
        assert group == "testgroup"

    def test_mocking_win32_exception_fallback(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """
        **Topic:** Advanced Mocking (Windows Exception Fallback)<br>
        **Focus:** Verifying error handling when win32security fails unexpectedly.\n
        ----------------------------------------------------------------------------------------------------
        We simulate an exception raised by `win32security.GetFileSecurity` to verify the fallback.
        """

        test_file = tmp_path / "win_fallback_test.txt"
        test_file.touch()

        monkeypatch.setattr("sys.platform", "win32")
        mock_win32 = MagicMock()
        mock_win32.GetFileSecurity.side_effect = RuntimeError("Access Denied")
        monkeypatch.setitem(sys.modules, "win32security", mock_win32)
        monkeypatch.setattr(Path, "owner", lambda self: "fallback_owner")  # pyright:ignore[reportUnknownArgumentType,reportUnknownLambdaType]

        owner, group = get_owner_group(test_file)
        assert owner == "fallback_owner"
        assert group is None
