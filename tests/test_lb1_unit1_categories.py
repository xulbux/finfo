import re
from datetime import datetime
from pathlib import Path
from helpers.display import format_relative_time
from helpers.extractors import get_file_info, get_folder_info


class TestCategory1:
    """
    **LB1:** Unit Test 1 – Test Categories 1-4<br>
    **Topics:** Error Handling, Regex, Combinatorial Logic, Collections
    """

    def test_error_handling_edge_cases(self) -> None:
        """
        **Topic:** Error Handling & Edge Cases<br>
        **Focus:** Targeted interception of exceptions and invalid values.\n
        ----------------------------------------------------------------------------------------------------
        File does not exist.<br>
        `get_file_info()` should not crash, but catch the OSError and set hashes to None.
        """

        missing_path = Path("this_file_does_not_exist_12345.xyz")

        # Test runs without raising exception despite the file missing:
        result = get_file_info(missing_path)

        # Verify exception handler worked:
        assert result["hashes"] is None
        assert result["is_executable"] is False

    def test_format_pattern_regex(self, tmp_path: Path) -> None:
        """
        **Topic:** Format & Pattern (Regex)<br>
        **Focus:** String validation via patterns.\n
        ----------------------------------------------------------------------------------------------------
        A real file is hashed. The return values must exactly match<br>
        the Regex for MD5, SHA1 and SHA256 (hex strings of correct length).
        """

        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello World")

        result = get_file_info(test_file)
        hashes = result["hashes"]

        assert hashes is not None
        assert hashes["md5"] is not None
        assert hashes["sha1"] is not None
        assert hashes["sha256"] is not None

        # [MD5] 32 hex chars:
        assert re.match(r"^[a-f0-9]{32}$", hashes["md5"]), "MD5 matched not the expected regex pattern"
        # [SHA1] 40 hex chars:
        assert re.match(r"^[a-f0-9]{40}$", hashes["sha1"]), "SHA1 matched not the expected regex pattern"
        # [SHA256] 64 hex chars:
        assert re.match(r"^[a-f0-9]{64}$", hashes["sha256"]), "SHA256 matched not the expected regex pattern"

    def test_combinatorial_logic(self) -> None:
        """
        **Topic:** Combinatorial Logic<br>
        **Focus:** Linked conditions and decision tables.\n
        ----------------------------------------------------------------------------------------------------
        `format_relative_time` has several if/elif conditions based on `delta.days`.<br>
        We check all possible decision branches (including boundary values and None handling).
        """

        # [0] `None` input:
        assert format_relative_time(None) is None

        ref_time = datetime(2026, 8, 18, 12, 0, 0)

        # [1] days == 0 (today):
        dt_today = datetime(2026, 8, 18, 10, 30, 0)
        assert format_relative_time(dt_today, reference_time=ref_time) == "at 10:30, today"

        # [2] days == 1 (yesterday):
        dt_yesterday = datetime(2026, 8, 17, 9, 15, 0)
        assert format_relative_time(dt_yesterday, reference_time=ref_time) == "at 09:15, yesterday"

        # [3] days > 1 (past):
        dt_past = datetime(2026, 8, 15, 8, 0, 0)
        assert format_relative_time(dt_past, reference_time=ref_time) == "at 08:00, 3 days ago"

        # [4] negative days, exactly 1 (tomorrow):
        dt_tomorrow = datetime(2026, 8, 19, 10, 0, 0)
        assert format_relative_time(dt_tomorrow, reference_time=ref_time) == "at 10:00, tomorrow"

        # [5] negative days, > 1 (in future):
        dt_future = datetime(2026, 8, 23, 12, 0, 0)
        assert format_relative_time(dt_future, reference_time=ref_time) == "at 12:00, in 5 days"

    def test_collections_lists(self, tmp_path: Path) -> None:
        """
        **Topic:** Collections & Lists<br>
        **Focus:** Testing arrays/lists (here: directory tree walking).\n
        ----------------------------------------------------------------------------------------------------
        We test both an empty directory structure and a multi-level nested folder structure.
        """

        # [1] Empty folder edge case (0 files, 0 subfolders, depth 0):
        empty_dir = tmp_path / "empty_folder"
        empty_dir.mkdir()
        empty_info = get_folder_info(empty_dir)
        assert empty_info["file_count"] == 0
        assert empty_info["sub_folder_count"] == 0
        assert empty_info["max_depth"] == 0

        # [2] Nested folder structure:
        # nested/
        # ├─ file1.txt
        # ├─ sub1/
        # │  ├─ file2.txt
        # │  └─ file3.txt
        # └─ sub2/
        #    └─ sub3/
        #       └─ file4.txt
        nested_dir = tmp_path / "nested"
        nested_dir.mkdir()
        (nested_dir / "file1.txt").touch()

        sub1 = nested_dir / "sub1"
        sub1.mkdir()
        (sub1 / "file2.txt").touch()
        (sub1 / "file3.txt").touch()

        sub2 = nested_dir / "sub2"
        sub2.mkdir()

        sub3 = sub2 / "sub3"
        sub3.mkdir()
        (sub3 / "file4.txt").touch()

        info = get_folder_info(nested_dir)

        # 4 files:
        assert info["file_count"] == 4
        # 3 subfolders:
        assert info["sub_folder_count"] == 3
        # Max depth is 2 (sub2/sub3):
        assert info["max_depth"] == 2
