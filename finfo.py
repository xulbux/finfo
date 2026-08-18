from pathlib import Path
import xulbux as xx

ARGS = xx.console.get_args({"path": "before"})


if __name__ == "__main__":
    path = Path(ARGS.path.get(0, "."))
