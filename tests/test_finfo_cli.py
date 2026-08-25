import zipfile
from pathlib import Path
from finfo import process_path
import pytest
from PIL import Image


class TestFinfoCli:
    """Tests for the main process_path routing logic in finfo.py."""

    def test_process_path_non_existent(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        missing = tmp_path / "non_existent_file.xyz"
        process_path(missing)
        out = capsys.readouterr().out
        assert "Error: The path" in out
        assert "does not exist." in out

    def test_process_path_directory(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        (tmp_path / "sub_file.txt").touch()
        process_path(tmp_path)
        out = capsys.readouterr().out
        assert "GENERAL INFORMATION" in out
        assert "FOLDER INFORMATION" in out

    def test_process_path_text_file(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        py_file = tmp_path / "script.py"
        py_file.write_text("print('hello world')", encoding="utf-8")
        process_path(py_file)
        out = capsys.readouterr().out
        assert "FILE INFORMATION" in out
        assert "TEXT INFORMATION" in out

    def test_process_path_document_file(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        doc_file = tmp_path / "report.pdf"
        doc_file.touch()
        process_path(doc_file)
        out = capsys.readouterr().out
        assert "FILE INFORMATION" in out
        assert "DOCUMENT INFORMATION" in out

    def test_process_path_executable_file(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        exe_file = tmp_path / "program.exe"
        exe_file.touch()
        process_path(exe_file)
        out = capsys.readouterr().out
        assert "FILE INFORMATION" in out
        assert "EXECUTABLE INFORMATION" in out

    def test_process_path_media_file(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        media_file = tmp_path / "picture.png"
        img = Image.new("RGB", (10, 10))
        img.save(media_file)
        process_path(media_file)
        out = capsys.readouterr().out
        assert "FILE INFORMATION" in out
        assert "MEDIA INFORMATION" in out

    def test_process_path_archive_file(self, capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
        zip_file = tmp_path / "bundle.zip"
        with zipfile.ZipFile(zip_file, "w") as z:
            z.writestr("test.txt", "content")
        process_path(zip_file)
        out = capsys.readouterr().out
        assert "FILE INFORMATION" in out
        assert "ARCHIVE INFORMATION" in out
