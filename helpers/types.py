from datetime import datetime
from pathlib import Path
from typing import TypedDict


class Permissions(TypedDict):
    symbolic: str
    """The symbolic representation of the file permissions (e.g., `rwxr-xr-x`)."""
    numeric: str
    """The numeric representation of the file permissions (e.g., `755`)."""


class GeneralInfo(TypedDict):
    abs_path: Path
    """The absolute path of the file or folder."""
    permissions: Permissions
    """The file or folder permissions."""
    owner: str | None
    """The owner of the file or folder."""
    group: str | None
    """The group of the file or folder."""
    created_at: datetime | None
    """The creation date and time."""
    updated_at: datetime | None
    """The last-updated date and time."""
    accessed_at: datetime | None
    """The last-accessed date and time."""
    disk_usage: int | None
    """The disk usage in bytes."""
    actual_size: int | None
    """The actual size in bytes."""
    is_hidden: bool | None
    """Whether the file or folder is hidden."""


class GeneralFolderInfo(TypedDict):
    file_count: int | None
    """The number of files within the folder."""
    sub_folder_count: int | None
    """The number of sub-folders within the folder."""
    max_depth: int | None
    """The maximum depth of the folder."""


class Hashes(TypedDict):
    md5: str | None
    """The MD5 checksum."""
    sha1: str | None
    """The SHA-1 checksum."""
    sha256: str | None
    """The SHA-256 checksum."""


class GeneralFileInfo(TypedDict):
    extension: str | None
    """The file extension."""
    mime_type: str | None
    """The MIME type or file type."""
    hashes: Hashes | None
    """The file hashes or checksums."""
    is_executable: bool | None
    """Whether the file is executable."""


class TextFileInfo(TypedDict):
    syntax: str | None
    """The syntax or programming language of the file."""
    encoding: str | None
    """The character encoding of the file."""
    line_count: int | None
    """The number of lines in the file."""
    char_count: int | None
    """The number of characters in the file."""


class DocumentFileInfo(TypedDict):
    page_count: int | None
    """The number of pages in the document."""
    word_count: int | None
    """The number of words in the document."""
    author: str | None
    """The author or creator of the document."""


class ExecutableFileInfo(TypedDict):
    architecture: str | None
    """The target architecture (e.g., `x86`, `x64`, `ARM`)."""
    bitness: int | None
    """The bitness (e.g., `32`, `64`)."""
    is_signed: bool | None
    """Whether the executable is signed."""


class Resolution(TypedDict):
    width: int | None
    """The width in pixels."""
    height: int | None
    """The height in pixels."""


class AudioInfo(TypedDict):
    sample_rate: int | None
    """The sample rate in Hz (e.g., 44100)."""
    channels: str | None
    """The channel setup (e.g., `mono`, `stereo`, `5.1`)."""


class ExifData(TypedDict):
    camera_model: str | None
    """The camera model used to take the photo."""
    date_taken: datetime | None
    """The date and time the photo was taken."""
    gps_coordinates: tuple[float, float] | None
    """The GPS coordinates as a (latitude, longitude) tuple."""


class MetadataTags(TypedDict):
    title: str | None
    """The title metadata tag."""
    artist: str | None
    """The artist metadata tag."""
    album: str | None
    """The album metadata tag."""


class MediaFileInfo(TypedDict):
    resolution: Resolution | None
    """The resolution of the media."""
    aspect_ratio: str | None
    """The aspect ratio of the media."""
    color_depth: int | None
    """The color depth of the media."""
    video_codec: str | None
    """The video codec (e.g., `H.264`, `HEVC`)."""
    audio_codec: str | None
    """The audio codec (e.g., `AAC`, `FLAC`)."""
    length_time: float | None
    """The length in seconds."""
    length_frames: int | None
    """The length in frames."""
    fps: float | None
    """The frames per second."""
    bitrate: int | None
    """The bitrate in bits per second (bps)."""
    audio_info: AudioInfo | None
    """Detailed audio information."""
    exif_data: ExifData | None
    """EXIF data from the media file."""
    metadata_tags: MetadataTags | None
    """Metadata tags like title, artist, and album."""


class ArchiveFileInfo(TypedDict):
    compression_type: str | None
    """The compression type (e.g., `Deflate`, `LZMA`)."""
    compression_ratio: float | None
    """The compression ratio."""
    item_count: int | None
    """The number of items contained within the archive."""
