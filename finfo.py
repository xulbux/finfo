from pathlib import Path
from helpers.types import GeneralInfo
import xulbux as xx

ARGS = xx.console.get_args({"path": "before"})


def get_general_info(path: Path) -> GeneralInfo:
    if not path.exists():
        raise FileNotFoundError(f"The path '{path}' does not exist.")

    ...

    return general_info


if __name__ == "__main__":
    path = Path(ARGS.path.get(0, "."))

    ...
