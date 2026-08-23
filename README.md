
# F-Info

<br>

## Dependency Installation

If you're on a Linux or macOS system, first create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate
```

Then, install the required dependencies:

```bash
python install_deps.py
```

<br>

## Information Categories

#### General

*   Absolute path
*   Permissions (human-readable: `rwxr-xr-x` and octal: `755`)
*   Owner / group
*   Relative creation date/time
*   Relative last-updated date/time
*   Relative last-accessed date/time
*   Disk usage vs. actual size
*   Hidden status

#### General Folders

*   File count
*   Sub-folder count
*   Max depth

#### General Files

*   Extension
*   Type / mime type
*   Hashes / checksums
*   Executable status

#### Text Files

*   Syntax / language
*   Encoding
*   Line count
*   Char count

#### Document Files

*   Page count
*   Word count
*   Author / creator

#### Executable Files

*   Architecture (`x86`, `x64`, `ARM`, …)
*   Bitness (`32-bit`, `64-bit`)
*   Signed status

#### Media Files

*   Resolution
*   Aspect ratio
*   Color depth
*   Codec (video: `H.264`, `HEVC`, … | audio: `AAC`, `FLAC`, …)
*   Lenght (time, frames)
*   FPS
*   Bitrate
*   Audio info (sample rate: `44.1 kHz`, … | channels: `mono`, `stereo, 5.1`, …)
*   EXIF Data (camera model, date taken, GPS coordinates)
*   Metadata tags (title, artist, album, …)

#### Archive Files

*   Compression type (`Deflate`, `LZMA`, …)
*   Compression ratio
*   Item count
