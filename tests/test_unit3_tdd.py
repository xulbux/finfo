from pathlib import Path
from helpers.extractors import get_entropy_info
import pytest


class TestCategory3:
    """
    LB1: Unit Test 3 - Test-Driven-Development (TDD)

    Feature: Entropy calculation for files to determine
    if a file is compressed or encrypted.
    """

    def test_get_entropy_info(self, tmp_path: Path) -> None:
        """
        Scenario: We create two files. One with very repetitive
        data (low entropy) and one with random/compressed
        data (high entropy).
        """
        low_entropy_file = tmp_path / "low.txt"
        # 1000x the letter 'A' - Entropy should be 0.0
        low_entropy_file.write_text("A" * 1000)

        result_low = get_entropy_info(low_entropy_file)
        assert result_low["entropy"] == pytest.approx(0.0)
        assert result_low["is_encrypted_or_compressed"] is False

        high_entropy_file = tmp_path / "high.bin"
        # Pseudo-random bytes (evenly distributed from 0-255)
        # The entropy should be very close to 8.0
        random_bytes = bytes([i % 256 for i in range(10000)])
        high_entropy_file.write_bytes(random_bytes)

        result_high = get_entropy_info(high_entropy_file)
        # The intentional bug in the code will trigger here!
        # The code incorrectly always returns "False" or calculates wrongly.
        assert result_high["entropy"] > 7.5
        assert result_high["is_encrypted_or_compressed"] is True
