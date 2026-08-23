#!/usr/bin/env python3
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, cast


def get_venv_python(project_dir: Path) -> Path | None:
    """Return the path to the Python binary in the virtual<br>
    environment if it exists, otherwise return `None`."""

    if not (venv_dir := project_dir / ".venv").is_dir():
        return None

    if sys.platform == "win32":
        venv_py = venv_dir / "Scripts" / "python.exe"
    else:
        venv_py = venv_dir / "bin" / "python"

    return venv_py if venv_py.is_file() else None


def ensure_running_in_venv(project_dir: Path) -> None:
    if not (venv_py := get_venv_python(project_dir)):
        return

    # Check if current Python matches the `.venv` Python binary:
    if Path(sys.executable).resolve() != venv_py.resolve():
        print(f"[*] Re-launching script inside virtualenv: {venv_py}")

        try:
            res = subprocess.run([str(venv_py), __file__, *sys.argv[1:]])
            raise SystemExit(res.returncode)
        except KeyboardInterrupt as exc:
            raise SystemExit(130) from exc


def extract_requirements(pyproject_path: Path) -> list[str]:
    """Extracts the list of dependencies from a `pyproject.toml` file."""

    try:
        with open(pyproject_path, "rb") as file:
            data = tomllib.load(file)

        project = cast("dict[str, Any]", data.get("project", {}))

        deps: list[str] = [str(dep) for dep in project.get("dependencies", []) if isinstance(dep, str)]
        dev_deps: list[str] = [
            str(dep) for dep in project.get("optional-dependencies", {}).get("dev", []) if isinstance(dep, str)
        ]

        return deps + dev_deps

    except Exception:
        pass

    # Basic line-parsing fallback if running on <3.11 without `tomli`:
    requirements: list[str] = []
    in_deps = False

    with open(pyproject_path, encoding="utf-8") as file:
        for line in file:
            if line.startswith("dependencies = [") or "dev = [" in (line := line.strip()):
                in_deps = True
                continue

            if in_deps:
                if line.endswith("]"):
                    in_deps = False
                if (cleaned := line.strip(",\"'[] ")) and not cleaned.startswith("#"):
                    requirements.append(cleaned)

    return requirements


def main() -> None:
    ensure_running_in_venv(root := Path(__file__).resolve().parent)

    if not (pyproject_file := root / "pyproject.toml").is_file():
        print(f"\n[!] Error: 'pyproject.toml' not found in {root}\n")
        raise SystemExit(1)

    if not (requirements := extract_requirements(pyproject_file)):
        print("\n[*] No dependencies found in 'pyproject.toml'.\n")
        return

    print(f"\n[*] Found {len(requirements)} packages to process.\n")

    failed: list[str] = []
    succeeded: list[str] = []

    for req in requirements:
        print(f"==> Installing: {req}")
        result = subprocess.run([sys.executable, "-m", "pip", "install", req])

        if result.returncode == 0:
            succeeded.append(req)
        else:
            print(f"[!] Failed to install: {req} (Skipping...)\n")
            failed.append(req)

    print(f"\n{'-' * 50}")
    print(f"[✓] Installed: {len(succeeded)}")

    if failed:
        print(f"[✗] Failed/Skipped ({len(failed)}):")
        for req in failed:
            print(f"    - {req}")

    print()


if __name__ == "__main__":
    main()
