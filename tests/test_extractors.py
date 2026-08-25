import io
import sys
import tarfile
import zipfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from helpers.extractors import (
    _get_image_info,
    _get_mutagen_info,
    _get_pymediainfo_info,
    _get_tar_info,
    _get_zip_info,
    get_archive_info,
    get_document_info,
    get_executable_info,
    get_folder_info,
    get_general_info,
    get_media_info,
    get_permissions,
    get_text_info,
)
import pytest
from PIL import Image


class TestExtractors:
    """Comprehensive tests for all extractor helper functions in helpers/extractors.py."""

    # ----------------------------------------------------------------------------------
    # 1. Permissions & General Info
    # ----------------------------------------------------------------------------------
    def test_get_permissions_file_and_dir(self, tmp_path: Path) -> None:
        file_path = tmp_path / "sample.txt"
        file_path.touch()
        file_perm = get_permissions(file_path)
        assert file_perm["symbolic"].startswith("-")
        assert len(file_perm["numeric"]) >= 3

        dir_perm = get_permissions(tmp_path)
        assert dir_perm["symbolic"].startswith("d")

    def test_get_general_info_regular_and_hidden(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        test_file = tmp_path / "regular.txt"
        test_file.write_text("General info content")

        info = get_general_info(test_file)
        assert info["actual_size"] == len("General info content")
        assert isinstance(info["created_at"], datetime)
        assert isinstance(info["updated_at"], datetime)
        assert isinstance(info["accessed_at"], datetime)
        assert info["is_hidden"] is False

        # Test hidden file on POSIX:
        hidden_file = tmp_path / ".hidden.txt"
        hidden_file.touch()
        monkeypatch.setattr("sys.platform", "linux")
        posix_info = get_general_info(hidden_file)
        assert posix_info["is_hidden"] is True

        # Test disk usage on POSIX with st_blocks:
        mock_stat = MagicMock()
        mock_stat.st_ctime = 1700000000.0
        mock_stat.st_mtime = 1700000000.0
        mock_stat.st_atime = 1700000000.0
        mock_stat.st_size = 1000
        mock_stat.st_blocks = 8
        mock_stat.st_mode = 0o100644
        monkeypatch.setattr(Path, "stat", lambda self: mock_stat)  # type:ignore[reportUnknownArgumentType]
        posix_blocks_info = get_general_info(test_file)
        assert posix_blocks_info["disk_usage"] == 4096

        # Test Windows ctypes hidden attribute fallback:
        monkeypatch.setattr("sys.platform", "win32")
        mock_ctypes = MagicMock()
        mock_ctypes.windll.kernel32.GetFileAttributesW.return_value = 2  # FILE_ATTRIBUTE_HIDDEN
        monkeypatch.setitem(sys.modules, "ctypes", mock_ctypes)
        win_info = get_general_info(test_file)
        assert win_info["is_hidden"] is True

        # Test Windows ctypes exception:
        mock_ctypes.windll.kernel32.GetFileAttributesW.side_effect = RuntimeError("Kernel32 error")
        win_err_info = get_general_info(test_file)
        assert win_err_info["is_hidden"] is False

    def test_get_folder_info_permission_error(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        def mock_walk(path: str):
            raise PermissionError("Access denied")

        monkeypatch.setattr("os.walk", mock_walk)
        info = get_folder_info(tmp_path)
        assert info["file_count"] == 0
        assert info["sub_folder_count"] == 0
        assert info["max_depth"] == 0

    # ----------------------------------------------------------------------------------
    # 2. Text Info
    # ----------------------------------------------------------------------------------
    def test_get_text_info_syntax_and_encoding(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        syntax_extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".html": "HTML",
            ".css": "CSS",
            ".json": "JSON",
            ".md": "Markdown",
            ".xml": "XML",
            ".sh": "Shell",
            ".c": "C",
            ".cpp": "C++",
            ".rs": "Rust",
            ".go": "Go",
            ".java": "Java",
            ".cs": "C#",
        }

        for ext, expected_syntax in syntax_extensions.items():
            f = tmp_path / f"test{ext}"
            f.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
            text_info = get_text_info(f)
            assert text_info["syntax"] == expected_syntax
            assert text_info["line_count"] == 3
            assert text_info["char_count"] and text_info["char_count"] > 0
            assert text_info["encoding"] is not None

        # Chardet returning None encoding (falls back to utf-8):
        mock_chardet = MagicMock()
        mock_chardet.detect.return_value = {"encoding": None}
        monkeypatch.setitem(sys.modules, "chardet", mock_chardet)
        fallback_file = tmp_path / "fallback.txt"
        fallback_file.write_text("plain", encoding="utf-8")
        assert get_text_info(fallback_file)["encoding"] == "utf-8"

        # Unknown extension:
        unknown_file = tmp_path / "unknown.xyz"
        unknown_file.write_text("hello", encoding="utf-8")
        assert get_text_info(unknown_file)["syntax"] is None

        # Non-existing file:
        missing_file = tmp_path / "missing_text.txt"
        assert get_text_info(missing_file)["line_count"] == 0

    # ----------------------------------------------------------------------------------
    # 3. Document Info (PDF)
    # ----------------------------------------------------------------------------------
    def test_get_document_info_pdf_and_non_pdf(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        # Non-PDF:
        txt_file = tmp_path / "doc.txt"
        txt_file.touch()
        assert get_document_info(txt_file) == {"page_count": None, "word_count": None, "author": None}

        # Mocked PDF with metadata:
        pdf_file = tmp_path / "sample.pdf"
        pdf_file.touch()

        mock_fitz = MagicMock()
        mock_doc = MagicMock()
        mock_doc.page_count = 2
        mock_doc.metadata = {"author": "Max Mustermann"}
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Hello world from page one"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Second page with text"
        mock_doc.__iter__.return_value = [mock_page1, mock_page2]
        mock_fitz.open.return_value = mock_doc

        monkeypatch.setitem(sys.modules, "fitz", mock_fitz)
        pdf_info = get_document_info(pdf_file)

        assert pdf_info["page_count"] == 2
        assert pdf_info["author"] == "Max Mustermann"
        assert pdf_info["word_count"] == 9
        assert mock_doc.close.called

        # Mocked PDF without metadata:
        mock_doc_no_meta = MagicMock()
        mock_doc_no_meta.page_count = 1
        mock_doc_no_meta.metadata = None
        mock_doc_no_meta.__iter__.return_value = []
        mock_fitz.open.return_value = mock_doc_no_meta
        no_meta_info = get_document_info(pdf_file)
        assert no_meta_info["author"] is None

        # PyMuPDF Exception handling:
        mock_fitz.open.side_effect = Exception("Corrupt PDF")
        err_pdf_info = get_document_info(pdf_file)
        assert err_pdf_info == {"page_count": None, "word_count": None, "author": None}

    # ----------------------------------------------------------------------------------
    # 4. Executable Info (PE)
    # ----------------------------------------------------------------------------------
    def test_get_executable_info_architectures(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        exe_file = tmp_path / "app.exe"
        exe_file.touch()

        mock_pefile = MagicMock()

        architectures = [
            (0x014C, "x86", 32),
            (0x8664, "x64", 64),
            (0x01C0, "ARM", 32),
            (0xAA64, "ARM64", 64),
            (0x9999, None, None),
        ]

        for machine_code, exp_arch, exp_bitness in architectures:
            mock_pe = MagicMock()
            mock_pe.FILE_HEADER.Machine = machine_code
            mock_pe.DIRECTORY_ENTRY_SECURITY = True
            mock_pefile.PE.return_value = mock_pe
            monkeypatch.setitem(sys.modules, "pefile", mock_pefile)

            res = get_executable_info(exe_file)
            assert res["architecture"] == exp_arch
            assert res["bitness"] == exp_bitness
            assert res["is_signed"] is True

        # PE with no FILE_HEADER:
        mock_pe_no_hdr = MagicMock()
        mock_pe_no_hdr.FILE_HEADER = None
        del mock_pe_no_hdr.DIRECTORY_ENTRY_SECURITY
        mock_pefile.PE.return_value = mock_pe_no_hdr
        res_no_hdr = get_executable_info(exe_file)
        assert res_no_hdr["architecture"] is None
        assert res_no_hdr["is_signed"] is False

        # Non-PE file error handling:
        mock_pefile.PE.side_effect = Exception("Not a PE file")
        monkeypatch.setitem(sys.modules, "pefile", mock_pefile)
        assert get_executable_info(exe_file) == {"architecture": None, "bitness": None, "is_signed": None}

    # ----------------------------------------------------------------------------------
    # 5. Media Info (Image, Audio, Video)
    # ----------------------------------------------------------------------------------
    def test_get_media_info_image_modes_and_exif(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        modes = ["1", "L", "P", "RGB", "RGBA"]
        for mode in modes:
            img_path = tmp_path / f"img_{mode}.png"
            img = Image.new(mode, (80, 60))
            img.save(img_path)
            res = get_media_info(img_path)
            assert res["resolution"] == {"width": 80, "height": 60}
            assert res["aspect_ratio"] == "4:3"
            assert res["color_depth"] is not None

        # Test CMYK and YCbCr modes via mocked Image:
        for mode, exp_depth in [("CMYK", 32), ("YCbCr", 24), ("I", 32), ("F", 32)]:
            mock_img = MagicMock()
            mock_img.width = 100
            mock_img.height = 50
            mock_img.mode = mode
            mock_img.getexif.return_value = {}
            mock_pil = MagicMock()
            mock_pil.Image.open.return_value.__enter__.return_value = mock_img
            monkeypatch.setitem(sys.modules, "PIL", mock_pil)
            monkeypatch.setitem(sys.modules, "PIL.Image", mock_pil.Image)

            res_mode: dict[str, object] = {}
            _get_image_info(tmp_path / "dummy.png", res_mode)
            assert res_mode["color_depth"] == exp_depth

        # Test EXIF parsing with extra tags and error handling:
        mock_img_exif = MagicMock()
        mock_img_exif.width = 1920
        mock_img_exif.height = 1080
        mock_img_exif.mode = "RGB"
        mock_img_exif.getexif.return_value = {272: "Canon EOS 80D", 306: "2026:08:18 14:30:00", 999: "Other"}
        mock_pil_exif = MagicMock()
        mock_pil_exif.Image.open.return_value.__enter__.return_value = mock_img_exif
        mock_pil_exif.ExifTags.TAGS = {272: "Model", 306: "DateTimeOriginal", 999: "UnknownTag"}
        monkeypatch.setitem(sys.modules, "PIL", mock_pil_exif)
        monkeypatch.setitem(sys.modules, "PIL.Image", mock_pil_exif.Image)
        monkeypatch.setitem(sys.modules, "PIL.ExifTags", mock_pil_exif.ExifTags)

        res_exif: dict[str, object] = {}
        _get_image_info(tmp_path / "dummy.jpg", res_exif)
        assert res_exif["exif_data"] is not None
        exif = res_exif["exif_data"]
        assert isinstance(exif, dict)
        assert exif["camera_model"] == "Canon EOS 80D"
        assert exif["date_taken"] == datetime(2026, 8, 18, 14, 30, 0)

        # Image exception handling:
        mock_pil_exif.Image.open.side_effect = Exception("Image load error")
        err_res: dict[str, object] = {}
        _get_image_info(tmp_path / "corrupt.jpg", err_res)
        assert "resolution" not in err_res

    def test_get_media_info_mutagen_channel_variations(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        audio_file = tmp_path / "test_channels.mp3"
        audio_file.touch()

        mock_mutagen = MagicMock()

        for ch, exp_str in [(1, "mono"), (2, "stereo"), (4, "4")]:
            mock_audio = MagicMock()
            mock_audio.info.length = 120.0
            mock_audio.info.bitrate = 192000
            mock_audio.info.sample_rate = 44100
            mock_audio.info.channels = ch
            mock_audio.tags = {"title": ["Song Title"], "artist": ["Artist"], "album": ["Album"]}
            mock_mutagen.File.return_value = mock_audio
            monkeypatch.setitem(sys.modules, "mutagen", mock_mutagen)

            res: dict[str, object] = {}
            _get_mutagen_info(audio_file, res)
            assert res["audio_info"] == {"sample_rate": 44100, "channels": exp_str}

        # Mutagen File returning None:
        mock_mutagen.File.return_value = None
        none_res: dict[str, object] = {}
        _get_mutagen_info(audio_file, none_res)
        assert "audio_info" not in none_res

        # Mutagen Exception:
        mock_mutagen.File.side_effect = Exception("Mutagen error")
        err_res: dict[str, object] = {}
        _get_mutagen_info(audio_file, err_res)
        assert "audio_info" not in err_res

    def test_get_media_info_pymediainfo_track_variations(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        media_file = tmp_path / "video.mp4"
        media_file.touch()

        mock_pmi = MagicMock()
        mock_video = MagicMock()
        mock_video.track_type = "Video"
        mock_video.width = 3840
        mock_video.height = 2160
        mock_video.frame_rate = 30.0
        mock_video.format = "HEVC"
        mock_video.frame_count = 1800
        mock_video.duration = 60000
        mock_video.display_aspect_ratio = "16:9"
        mock_video.bit_depth = 10

        for ch, exp_ch in [(1, "mono"), (2, "stereo"), (6, "5.1"), (8, "8")]:
            mock_audio = MagicMock()
            mock_audio.track_type = "Audio"
            mock_audio.format = "FLAC"
            mock_audio.bit_rate = 1411200
            mock_audio.sampling_rate = 96000
            mock_audio.channel_s = ch

            mock_pmi.MediaInfo.parse.return_value.tracks = [mock_video, mock_audio]
            monkeypatch.setitem(sys.modules, "pymediainfo", mock_pmi)

            res: dict[str, object] = {}
            _get_pymediainfo_info(media_file, res)
            assert res["video_codec"] == "HEVC"
            assert res["audio_codec"] == "FLAC"
            assert res["color_depth"] == 10
            assert res["audio_info"] == {"sample_rate": 96000, "channels": exp_ch}

        # PyMediaInfo exception:
        mock_pmi.MediaInfo.parse.side_effect = Exception("PyMediaInfo error")
        err_res: dict[str, object] = {}
        _get_pymediainfo_info(media_file, err_res)
        assert "video_codec" not in err_res

    # ----------------------------------------------------------------------------------
    # 6. Archive Info (ZIP & TAR methods)
    # ----------------------------------------------------------------------------------
    def test_get_archive_info_zip_methods(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        zip_path = tmp_path / "archive.zip"
        zip_path.touch()

        mock_zipfile = MagicMock()
        mock_zipfile.is_zipfile.return_value = True

        compressions = [
            (zipfile.ZIP_DEFLATED, "Deflate"),
            (zipfile.ZIP_LZMA, "LZMA"),
            (zipfile.ZIP_BZIP2, "BZIP2"),
            (zipfile.ZIP_STORED, "Stored"),
        ]

        for zip_method, exp_name in compressions:
            mock_info = MagicMock()
            mock_info.compress_type = zip_method
            mock_info.file_size = 200
            mock_info.compress_size = 100

            mock_zip = MagicMock()
            mock_zip.infolist.return_value = [mock_info]
            mock_zipfile.ZipFile.return_value.__enter__.return_value = mock_zip
            mock_zipfile.ZIP_DEFLATED = zipfile.ZIP_DEFLATED
            mock_zipfile.ZIP_LZMA = zipfile.ZIP_LZMA
            mock_zipfile.ZIP_BZIP2 = zipfile.ZIP_BZIP2
            mock_zipfile.ZIP_STORED = zipfile.ZIP_STORED
            monkeypatch.setitem(sys.modules, "zipfile", mock_zipfile)

            res = get_archive_info(zip_path)
            assert res["compression_type"] == exp_name
            assert res["item_count"] == 1
            assert res["compression_ratio"] == pytest.approx(2.0)

        # ZIP Exception:
        mock_zipfile.ZipFile.side_effect = Exception("Corrupt zip")
        err_res: dict[str, object] = {}
        _get_zip_info(zip_path, err_res)
        assert "compression_type" not in err_res

    def test_get_archive_info_tar_compression_extensions(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        tar_extensions = [
            (".tar.gz", "GZIP"),
            (".tar.bz2", "BZIP2"),
            (".tar.xz", "LZMA"),
            (".tar", "Uncompressed"),
        ]

        for ext, exp_type in tar_extensions:
            p = tmp_path / f"test{ext}"
            mode = "w:gz" if "gz" in ext else "w:bz2" if "bz2" in ext else "w:xz" if "xz" in ext else "w"
            with tarfile.open(p, mode) as t:
                data = b"Archive payload"
                ti = tarfile.TarInfo(name="item.txt")
                ti.size = len(data)
                t.addfile(ti, io.BytesIO(data))

            res = get_archive_info(p)
            assert res["compression_type"] == exp_type
            assert res["item_count"] == 1

        # Non-tar file:
        non_tar = tmp_path / "not_tar.txt"
        non_tar.touch()
        assert _get_tar_info(non_tar, {}) is False

        # TAR Exception:
        mock_tarfile = MagicMock()
        mock_tarfile.is_tarfile.return_value = True
        mock_tarfile.open.side_effect = Exception("Tar error")
        monkeypatch.setitem(sys.modules, "tarfile", mock_tarfile)
        err_res: dict[str, object] = {}
        _get_tar_info(non_tar, err_res)
        assert "compression_type" not in err_res
