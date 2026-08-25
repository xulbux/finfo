from collections.abc import Mapping
from datetime import datetime
from typing import Any


def format_relative_time(dt: datetime | None, reference_time: datetime | None = None) -> str | None:
    """Formats datetime relatively, e.g. 'at 14:30, 2 days ago'."""
    if not dt:
        return None

    if reference_time is None:
        reference_time = datetime.now()

    delta = reference_time - dt
    time_str = dt.strftime("%H:%M")
    days = delta.days

    if days == 0:
        return f"at {time_str}, today"
    elif days == 1:
        return f"at {time_str}, yesterday"
    elif days > 1:
        return f"at {time_str}, {days} days ago"
    else:
        # Negative days (in the future)
        future_days = abs(days)
        if future_days == 1:
            return f"at {time_str}, tomorrow"
        return f"at {time_str}, in {future_days} days"


def display_info(info_dict: Mapping[str, Any], title: str = "Info"):
    """Nicely prints the dictionary to the console."""
    print(f"\n--- {title.upper()} ---")

    def print_dict(d: Mapping[str, Any], indent: int = 0):
        for k, v in d.items():
            if v is None:
                continue

            pad = " " * indent
            key_name = k.replace("_", " ").title()

            if isinstance(v, dict) or (hasattr(v, "items") and callable(v.items)):
                print(f"{pad}{key_name}:")
                print_dict(v, indent + 2)  # type:ignore
            elif isinstance(v, datetime):
                # The prompt asked for "Created at hh:mm, X days ago"
                # Since the key itself says 'Created At', it will render as 'Created At: at 14:30, 2 days ago'
                # Let's just return the time and drop 'at' if the key implies it, but sticking to format is fine
                print(f"{pad}{key_name}: {format_relative_time(v)}")
            else:
                print(f"{pad}{key_name}: {v}")

    print_dict(info_dict)
    print("-" * (8 + len(title)))
