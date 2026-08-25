from pathlib import Path
from helpers.display import display_info
from helpers.extractors import (
    get_archive_info,
    get_document_info,
    get_executable_info,
    get_file_info,
    get_folder_info,
    get_general_info,
    get_media_info,
    get_text_info,
)
from xulbux import ArgumentParser


def process_path(path: Path):
    if not path.exists():
        print(f"Error: The path '{path}' does not exist.")
        return

    # 1. General Info (Always applicable)
    gen_info = get_general_info(path)
    display_info(gen_info, "General Information")

    if path.is_dir():
        folder_info = get_folder_info(path)
        display_info(folder_info, "Folder Information")
    else:
        # General File Info
        file_info = get_file_info(path)
        display_info(file_info, "File Information")

        mime = file_info.get("mime_type") or ""
        ext = (file_info.get("extension") or "").lower()

        # Determine specific types based on mime or extension
        is_text = mime.startswith("text/") or ext in (
            ".json",
            ".xml",
            ".md",
            ".csv",
            ".py",
            ".js",
            ".ts",
            ".c",
            ".cpp",
            ".rs",
            ".go",
        )
        is_doc = mime == "application/pdf" or ext in (".pdf", ".docx", ".doc", ".odt")
        is_exec = mime in ("application/x-msdownload", "application/x-dosexec") or ext in (".exe", ".dll", ".sys")
        is_media = mime.startswith("image/") or mime.startswith("video/") or mime.startswith("audio/")
        is_archive = mime in (
            "application/zip",
            "application/x-tar",
            "application/gzip",
            "application/x-bzip2",
            "application/x-xz",
        ) or ext in (".zip", ".tar", ".gz", ".tgz", ".bz2", ".tbz", ".xz", ".txz")

        if is_text:
            text_info = get_text_info(path)
            display_info(text_info, "Text Information")

        if is_doc:
            doc_info = get_document_info(path)
            display_info(doc_info, "Document Information")

        if is_exec:
            exec_info = get_executable_info(path)
            display_info(exec_info, "Executable Information")

        if is_media:
            media_info = get_media_info(path)
            display_info(media_info, "Media Information")

        if is_archive:
            archive_info = get_archive_info(path)
            display_info(archive_info, "Archive Information")

    print()


if __name__ == "__main__":
    args = ArgumentParser(
        title="F-Info",
        subtitle="Quickly retrieve and inspect detailed information for files/folders",
        controls=[("Ctrl+C", "Cancel and exit")],
    )

    args.add_arg("path", required=False, help="Path to the file or folder to analyze")

    global ARGS
    ARGS = args.parse()

    target_path = Path(ARGS.path.val(Path, Path.cwd()))

    process_path(target_path)
