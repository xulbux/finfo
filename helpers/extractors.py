import hashlib
import math
import mimetypes
import os
import stat
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, cast
from helpers.types import (
    ArchiveFileInfo,
    DocumentFileInfo,
    EntropyFileInfo,
    ExecutableFileInfo,
    GeneralFileInfo,
    GeneralFolderInfo,
    GeneralInfo,
    Hashes,
    MediaFileInfo,
    Permissions,
    TextFileInfo,
)


def get_permissions(path: Path) -> Permissions:
    """Gets the symbolic and numeric permissions of a file."""
    st = path.stat()
    mode = st.st_mode

    numeric = oct(mode & 0o777)[2:]
    is_dir = stat.S_ISDIR(mode)
    sym = "d" if is_dir else "-"
    for who in "USR", "GRP", "OTH":
        for what in "R", "W", "X":
            if mode & getattr(stat, f"S_I{what}{who}"):
                sym += what.lower()
            else:
                sym += "-"

    return {"symbolic": sym, "numeric": numeric}


def get_owner_group(path: Path) -> tuple[str | None, str | None]:
    """Gets owner and group of a file, cross-platform."""
    import contextlib

    owner: str | None = None
    group: str | None = None
    if sys.platform == "win32":
        try:
            import win32security

            sd = win32security.GetFileSecurity(
                str(path), win32security.OWNER_SECURITY_INFORMATION | win32security.GROUP_SECURITY_INFORMATION
            )
            owner_sid = sd.GetSecurityDescriptorOwner()
            group_sid = sd.GetSecurityDescriptorGroup()  # type: ignore
            owner_name, owner_domain, _ = win32security.LookupAccountSid(None, cast("Any", owner_sid))
            group_name, group_domain, _ = win32security.LookupAccountSid(None, cast("Any", group_sid))
            owner = f"{owner_domain}\\{owner_name}"
            group = f"{group_domain}\\{group_name}"
        except Exception:
            with contextlib.suppress(Exception):
                owner = cast("str", path.owner())  # type: ignore
    else:
        with contextlib.suppress(Exception):
            owner = cast("str", path.owner())  # type: ignore
        with contextlib.suppress(Exception):
            group = cast("str", path.group())  # type: ignore

    return owner, group


def get_general_info(path: Path) -> GeneralInfo:
    """Extracts general file/folder information like permissions, dates, size, and owner."""
    st = path.stat()
    owner, group = get_owner_group(path)

    created_at = datetime.fromtimestamp(st.st_ctime)
    updated_at = datetime.fromtimestamp(st.st_mtime)
    accessed_at = datetime.fromtimestamp(st.st_atime)

    actual_size = st.st_size
    if sys.platform == "win32":
        disk_usage = actual_size  # Approximation on Windows without heavier API calls
    else:
        disk_usage = st.st_blocks * 512 if hasattr(st, "st_blocks") else actual_size

    is_hidden = False
    if sys.platform == "win32":
        try:
            import ctypes

            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            is_hidden = bool(attrs & 2)
        except Exception:
            pass
    else:
        is_hidden = path.name.startswith(".")

    return {
        "abs_path": path.resolve(),
        "permissions": get_permissions(path),
        "owner": owner,
        "group": group,
        "created_at": created_at,
        "updated_at": updated_at,
        "accessed_at": accessed_at,
        "disk_usage": disk_usage,
        "actual_size": actual_size,
        "is_hidden": is_hidden,
    }


def get_folder_info(path: Path) -> GeneralFolderInfo:
    """Recursively scans a folder to calculate file count, sub-folder count, and max depth."""
    file_count = 0
    sub_folder_count = 0
    max_depth = 0

    base_depth = len(path.resolve().parts)

    try:
        for root, dirs, files in os.walk(path):
            current_depth = len(Path(root).resolve().parts) - base_depth
            if current_depth > max_depth:
                max_depth = current_depth

            sub_folder_count += len(dirs)
            file_count += len(files)
    except PermissionError:
        pass

    return {"file_count": file_count, "sub_folder_count": sub_folder_count, "max_depth": max_depth}


def get_file_info(path: Path) -> GeneralFileInfo:
    """Extracts MIME type, hashes, and executable status."""
    mime_type, _ = mimetypes.guess_type(path)
    extension = path.suffix.lower() if path.suffix else None

    is_executable = os.access(path, os.X_OK)

    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()

    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
                sha1.update(chunk)
                sha256.update(chunk)
        hashes: Hashes | None = {"md5": md5.hexdigest(), "sha1": sha1.hexdigest(), "sha256": sha256.hexdigest()}
    except OSError:
        hashes = None

    return {"extension": extension, "mime_type": mime_type, "hashes": hashes, "is_executable": is_executable}


def get_text_info(path: Path) -> TextFileInfo:
    """Uses chardet to determine encoding and reads lines/chars."""
    import chardet

    encoding = None
    syntax = None
    line_count = 0
    char_count = 0

    try:
        with open(path, "rb") as f:
            raw = f.read(10000)
            result = chardet.detect(raw)
            encoding = result["encoding"]

        if not encoding:
            encoding = "utf-8"

        with open(path, encoding=encoding, errors="replace") as f:
            for line in f:
                line_count += 1
                char_count += len(line)

        ext = path.suffix.lower()
        syntax_map = {
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
        syntax = syntax_map.get(ext)
    except OSError:
        pass

    return {"syntax": syntax, "encoding": encoding, "line_count": line_count, "char_count": char_count}


def get_document_info(path: Path) -> DocumentFileInfo:
    """Uses PyMuPDF (fitz) to extract PDF page/word count and author."""
    page_count = None
    word_count = None
    author = None

    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            import fitz  # pyright: ignore[reportMissingTypeStubs]

            doc: Any = fitz.open(path)
            page_count = int(doc.page_count)
            if getattr(doc, "metadata", None):
                author = doc.metadata.get("author")  # type: ignore

            words = 0
            for page in doc:
                text = str(page.get_text())
                words += len(text.split())
            word_count = words
            doc.close()
        except Exception:
            pass

    return {"page_count": page_count, "word_count": word_count, "author": author}


def get_executable_info(path: Path) -> ExecutableFileInfo:
    """Extracts bitness and architecture of PE files (Windows executables)."""
    architecture = None
    bitness = None
    is_signed = None

    try:
        import pefile  # pyright: ignore[reportMissingTypeStubs]

        pe = pefile.PE(path)

        machine = None
        if getattr(pe, "FILE_HEADER", None):
            machine = getattr(pe.FILE_HEADER, "Machine", None)

        if machine == 0x014C:
            architecture = "x86"
            bitness = 32
        elif machine == 0x8664:
            architecture = "x64"
            bitness = 64
        elif machine == 0x01C0:
            architecture = "ARM"
            bitness = 32
        elif machine == 0xAA64:
            architecture = "ARM64"
            bitness = 64

        is_signed = hasattr(pe, "DIRECTORY_ENTRY_SECURITY")
        pe.close()
    except Exception:
        pass

    return {"architecture": architecture, "bitness": bitness, "is_signed": is_signed}


def _get_image_info(path: Path, result: dict[str, Any]) -> None:
    import contextlib

    try:
        from PIL import ExifTags, Image

        with Image.open(path) as img:
            img_any = cast("Any", img)
            result["resolution"] = {"width": img_any.width, "height": img_any.height}
            if img_any.height > 0:
                import math

                gcd = math.gcd(img_any.width, img_any.height)
                if gcd > 0:
                    result["aspect_ratio"] = f"{img_any.width // gcd}:{img_any.height // gcd}"

            mode_to_depth: dict[str, int] = {
                "1": 1,
                "L": 8,
                "P": 8,
                "RGB": 24,
                "RGBA": 32,
                "CMYK": 32,
                "YCbCr": 24,
                "I": 32,
                "F": 32,
            }
            result["color_depth"] = mode_to_depth.get(str(img_any.mode))

            exif: Any = img_any.getexif()
            if exif:
                camera_model: str | None = None
                date_taken: datetime | None = None
                gps_coords: tuple[float, float] | None = None

                for k, v in dict(exif).items():
                    tag: Any = ExifTags.TAGS.get(k, k)
                    if tag == "Model":
                        camera_model = str(v)
                    elif tag == "DateTimeOriginal":
                        with contextlib.suppress(ValueError):
                            date_taken = datetime.strptime(str(v), "%Y:%m:%d %H:%M:%S")

                result["exif_data"] = {"camera_model": camera_model, "date_taken": date_taken, "gps_coordinates": gps_coords}
    except Exception:
        pass


def _get_mutagen_info(path: Path, result: dict[str, Any]) -> None:
    try:
        import mutagen

        m_file: Any = cast("Any", mutagen).File(path)
        if m_file:
            if hasattr(m_file, "info"):
                if not result.get("length_time"):
                    result["length_time"] = float(m_file.info.length)
                if not result.get("bitrate"):
                    result["bitrate"] = getattr(m_file.info, "bitrate", None)
                sample_rate = getattr(m_file.info, "sample_rate", None)
                channels = getattr(m_file.info, "channels", None)
                if channels:
                    ch_str = "mono" if channels == 1 else "stereo" if channels == 2 else str(channels)
                    if not result.get("audio_info"):
                        result["audio_info"] = {"sample_rate": sample_rate, "channels": ch_str}

            if hasattr(m_file, "tags") and m_file.tags:
                title = m_file.tags.get("TIT2", m_file.tags.get("title", [None]))[0]
                artist = m_file.tags.get("TPE1", m_file.tags.get("artist", [None]))[0]
                album = m_file.tags.get("TALB", m_file.tags.get("album", [None]))[0]
                result["metadata_tags"] = {
                    "title": str(title) if title else None,
                    "artist": str(artist) if artist else None,
                    "album": str(album) if album else None,
                }
    except Exception:
        pass


def _get_pymediainfo_video(track: Any, result: dict[str, Any]) -> None:
    if not result.get("resolution") and track.width and track.height:
        result["resolution"] = {"width": int(track.width), "height": int(track.height)}
    if not result.get("fps") and track.frame_rate:
        result["fps"] = float(track.frame_rate)
    if not result.get("video_codec") and track.format:
        result["video_codec"] = str(track.format)
    if not result.get("length_frames") and track.frame_count:
        result["length_frames"] = int(track.frame_count)
    if not result.get("length_time") and track.duration:
        result["length_time"] = float(track.duration) / 1000.0
    if not result.get("aspect_ratio") and track.display_aspect_ratio:
        result["aspect_ratio"] = str(track.display_aspect_ratio)
    if not result.get("color_depth") and track.bit_depth:
        result["color_depth"] = int(track.bit_depth)


def _get_pymediainfo_audio(track: Any, result: dict[str, Any]) -> None:
    if not result.get("audio_codec") and track.format:
        result["audio_codec"] = str(track.format)
    if not result.get("bitrate") and track.bit_rate:
        result["bitrate"] = int(track.bit_rate)
    if not result.get("audio_info"):
        sr = int(track.sampling_rate) if track.sampling_rate else None
        ch = int(track.channel_s) if track.channel_s else None
        ch_str = None
        if ch == 1:
            ch_str = "mono"
        elif ch == 2:
            ch_str = "stereo"
        elif ch == 6:
            ch_str = "5.1"
        elif ch:
            ch_str = str(ch)
        result["audio_info"] = {"sample_rate": sr, "channels": ch_str}


def _get_pymediainfo_info(path: Path, result: dict[str, Any]) -> None:
    try:
        from pymediainfo import MediaInfo

        media_info: Any = MediaInfo.parse(path)
        for track in media_info.tracks:
            if track.track_type == "Video":
                _get_pymediainfo_video(track, result)
            elif track.track_type == "Audio":
                _get_pymediainfo_audio(track, result)
    except Exception:
        pass


def get_media_info(path: Path) -> MediaFileInfo:
    """Extracts media metadata using pymediainfo, Pillow, and mutagen."""
    result: dict[str, Any] = {
        "resolution": None,
        "aspect_ratio": None,
        "color_depth": None,
        "video_codec": None,
        "audio_codec": None,
        "length_time": None,
        "length_frames": None,
        "fps": None,
        "bitrate": None,
        "audio_info": None,
        "exif_data": None,
        "metadata_tags": None,
    }

    _get_image_info(path, result)
    _get_mutagen_info(path, result)
    _get_pymediainfo_info(path, result)

    return cast("MediaFileInfo", result)


def _get_zip_info(path: Path, result: dict[str, Any]) -> bool:
    import zipfile

    if not zipfile.is_zipfile(path):
        return False

    try:
        with zipfile.ZipFile(path, "r") as z:
            infos: Any = z.infolist()
            result["item_count"] = len(infos)

            uncompressed_size = sum(int(i.file_size) for i in infos)
            compressed_size = sum(int(i.compress_size) for i in infos)

            if uncompressed_size > 0:
                result["compression_ratio"] = float(uncompressed_size) / float(max(compressed_size, 1))

            methods: set[Any] = {i.compress_type for i in infos}
            if zipfile.ZIP_DEFLATED in methods:
                result["compression_type"] = "Deflate"
            elif zipfile.ZIP_LZMA in methods:
                result["compression_type"] = "LZMA"
            elif zipfile.ZIP_BZIP2 in methods:
                result["compression_type"] = "BZIP2"
            elif zipfile.ZIP_STORED in methods:
                result["compression_type"] = "Stored"
    except Exception:
        pass

    return True


def _get_tar_info(path: Path, result: dict[str, Any]) -> bool:
    import tarfile

    if not tarfile.is_tarfile(path):
        return False

    try:
        with tarfile.open(path, "r") as t:
            members: Any = t.getmembers()
            result["item_count"] = len(members)

        ext = path.suffix.lower()
        if ext in (".gz", ".tgz"):
            result["compression_type"] = "GZIP"
        elif ext in (".bz2", ".tbz"):
            result["compression_type"] = "BZIP2"
        elif ext in (".xz", ".txz"):
            result["compression_type"] = "LZMA"
        else:
            result["compression_type"] = "Uncompressed"
    except Exception:
        pass

    return True


def get_archive_info(path: Path) -> ArchiveFileInfo:
    """Extracts info for archives (ZIP, TAR)."""
    result: dict[str, Any] = {
        "compression_type": None,
        "compression_ratio": None,
        "item_count": None,
    }

    if not _get_zip_info(path, result):
        _get_tar_info(path, result)

    return cast("ArchiveFileInfo", result)


def get_entropy_info(path: Path) -> EntropyFileInfo:
    """Calculates the Shannon entropy of a file.\n
    ------------------------------------------------------------------------------------------
    `is_encrypted_or_compressed` always returns `False` as an intentional bug for TDD."""

    entropy: float = 0.0

    try:
        if data := path.read_bytes():
            length = len(data)
            entropy = -sum((count / length) * math.log2(count / length) for count in Counter(data).values())

    except OSError:
        pass

    return {
        "entropy": entropy,
        "is_encrypted_or_compressed": False,  # Hardcoded to `False` for TDD purposes.
    }
