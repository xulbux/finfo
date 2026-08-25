from pathlib import Path
from helpers.extractors import get_entropy_info
import pytest


class TestCategory3:
    """
    **LB1:** Unit Test 3 – Test-Driven-Development (TDD)<br>
    **Topics:** Entropy Calculation & Combinatorial Logic\n
    ----------------------------------------------------------------------------------------------------
    **Feature:** Entropy calculation for files to determine if a file is compressed or encrypted.
    """

    def test_get_entropy_info(self, tmp_path: Path) -> None:
        """
        **Topic:** Entropy Calculation & Combinatorial Logic<br>
        **Focus:** Testing the `get_entropy_info` function with low and high entropy files.\n
        ----------------------------------------------------------------------------------------------------
        We create two files. One with very repetitive data (low entropy)<br>
        and one with random/compressed data (high entropy).
        """

        low_entropy_file = tmp_path / "low.txt"
        # 1000x letter `A` => entropy should be `0.0`:
        low_entropy_file.write_text("A" * 1000)

        result_low = get_entropy_info(low_entropy_file)
        assert result_low["entropy"] == pytest.approx(0.0)
        assert result_low["is_encrypted_or_compressed"] is False

        high_entropy_file = tmp_path / "high.bin"
        # Pseudo-random bytes (evenly distributed from 0-255).
        # The entropy should be very close to `8.0`:
        random_bytes = bytes([i % 256 for i in range(10000)])
        high_entropy_file.write_bytes(random_bytes)

        result_high = get_entropy_info(high_entropy_file)
        assert result_high["entropy"] > 7.5
        assert result_high["is_encrypted_or_compressed"] is True

    def test_get_entropy_empty_and_missing_file(self, tmp_path: Path) -> None:
        """
        **Topic:** Entropy Edge Cases (Empty & Missing Files)<br>
        **Focus:** Testing boundary condition of zero bytes and missing files.\n
        ----------------------------------------------------------------------------------------------------
        Empty files or non-existent files must not crash and should return 0.0 entropy.
        """

        # [1] Empty file (0 bytes):
        empty_file = tmp_path / "empty.bin"
        empty_file.touch()
        result_empty = get_entropy_info(empty_file)
        assert result_empty["entropy"] == pytest.approx(0.0)
        assert result_empty["is_encrypted_or_compressed"] is False

        # [2] Missing file (`OSError`):
        missing_file = tmp_path / "does_not_exist.bin"
        result_missing = get_entropy_info(missing_file)
        assert result_missing["entropy"] == pytest.approx(0.0)
        assert result_missing["is_encrypted_or_compressed"] is False

    def test_get_entropy_natural_text(self, tmp_path: Path) -> None:
        """
        **Topic:** Entropy for Natural Language Text<br>
        **Focus:** Verifying mid-range entropy for ordinary text files.\n
        ----------------------------------------------------------------------------------------------------
        Normal text has an entropy between 3.5 and 5.0 (neither 0 nor > 7.5).
        """

        text_file = tmp_path / "prose.txt"
        text_file.write_text("The quick brown fox jumps over the lazy dog. Testing software and applications.")
        result_text = get_entropy_info(text_file)
        assert 3.0 < result_text["entropy"] < 6.0
        assert result_text["is_encrypted_or_compressed"] is False
