"""
Helper Functions

General-purpose utility functions for the Ghost-QC application.
"""

import json
import re
import unicodedata
from typing import Any, Dict, List, Optional, Union


def truncate_string(
    text: str,
    max_length: int,
    suffix: str = "...",
) -> str:
    """
    Truncate a string to a maximum length.

    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncated

    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def sanitize_filename(
    filename: str,
    replacement: str = "_",
    max_length: int = 255,
) -> str:
    """
    Sanitize a string for use as a filename.

    Args:
        filename: String to sanitize
        replacement: Character to replace invalid chars with
        max_length: Maximum filename length

    Returns:
        Sanitized filename
    """
    # Normalize unicode characters
    filename = unicodedata.normalize("NFKD", filename)
    filename = filename.encode("ascii", "ignore").decode("ascii")

    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing spaces and dots
    filename = filename.strip(" .")

    # Collapse multiple replacements
    filename = re.sub(f"{re.escape(replacement)}+", replacement, filename)

    # Truncate if necessary
    if len(filename) > max_length:
        name, ext = (
            (filename.rsplit(".", 1) + [""])[:2]
            if "." in filename
            else (filename, "")
        )
        max_name_length = max_length - len(ext) - (1 if ext else 0)
        filename = name[:max_name_length] + ("." + ext if ext else "")

    return filename or "unnamed"


def parse_duration(duration_str: str) -> float:
    """
    Parse a duration string to seconds.

    Supports formats like: "1h", "30m", "45s", "1h30m", "1.5h"

    Args:
        duration_str: Duration string

    Returns:
        Duration in seconds
    """
    if not duration_str:
        return 0.0

    # Try parsing as plain number (assumes seconds)
    try:
        return float(duration_str)
    except ValueError:
        pass

    total_seconds = 0.0
    duration_str = duration_str.lower().strip()

    # Match patterns like "1h", "30m", "45s"
    pattern = r"(\d+(?:\.\d+)?)\s*(h|hr|hour|hours|m|min|minute|minutes|s|sec|second|seconds)"
    matches = re.findall(pattern, duration_str)

    multipliers = {
        "h": 3600, "hr": 3600, "hour": 3600, "hours": 3600,
        "m": 60, "min": 60, "minute": 60, "minutes": 60,
        "s": 1, "sec": 1, "second": 1, "seconds": 1,
    }

    for value, unit in matches:
        total_seconds += float(value) * multipliers.get(unit, 1)

    return total_seconds


def format_duration(seconds: float, precision: int = 1) -> str:
    """
    Format seconds into human-readable duration.

    Args:
        seconds: Duration in seconds
        precision: Decimal places for seconds

    Returns:
        Formatted duration string
    """
    if seconds < 0:
        return "0s"

    parts = []

    hours = int(seconds // 3600)
    if hours > 0:
        parts.append(f"{hours}h")
        seconds %= 3600

    minutes = int(seconds // 60)
    if minutes > 0:
        parts.append(f"{minutes}m")
        seconds %= 60

    if seconds > 0 or not parts:
        if precision == 0:
            parts.append(f"{int(seconds)}s")
        else:
            parts.append(f"{seconds:.{precision}f}s")

    return " ".join(parts)


def merge_dicts(
    base: Dict[str, Any],
    override: Dict[str, Any],
    deep: bool = True,
) -> Dict[str, Any]:
    """
    Merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with override values
        deep: Perform deep merge for nested dicts

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if deep and key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value

    return result


def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON object from text that may contain other content.

    Args:
        text: Text that may contain JSON

    Returns:
        Parsed JSON dict or None
    """
    if not text:
        return None

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to extract from markdown code block
    code_block_match = re.search(
        r"```(?:json)?\s*(\{.*?\})\s*```",
        text,
        re.DOTALL,
    )
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object in text
    json_match = re.search(r"\{[^{}]*\}", text)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try to find nested JSON object
    brace_count = 0
    start_idx = None

    for i, char in enumerate(text):
        if char == "{":
            if start_idx is None:
                start_idx = i
            brace_count += 1
        elif char == "}":
            brace_count -= 1
            if brace_count == 0 and start_idx is not None:
                try:
                    return json.loads(text[start_idx:i + 1])
                except json.JSONDecodeError:
                    start_idx = None

    return None


def flatten_dict(
    d: Dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
) -> Dict[str, Any]:
    """
    Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Key prefix for nested items
        separator: Separator between key levels

    Returns:
        Flattened dictionary
    """
    items: List[tuple] = []

    for key, value in d.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key, separator).items())
        else:
            items.append((new_key, value))

    return dict(items)


def unflatten_dict(
    d: Dict[str, Any],
    separator: str = ".",
) -> Dict[str, Any]:
    """
    Unflatten a flattened dictionary.

    Args:
        d: Flattened dictionary
        separator: Separator used in keys

    Returns:
        Nested dictionary
    """
    result: Dict[str, Any] = {}

    for key, value in d.items():
        parts = key.split(separator)
        current = result

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(
    obj: Union[Dict[str, Any], List[Any]],
    *keys: Union[str, int],
    default: Any = None,
) -> Any:
    """
    Safely get a nested value from a dict or list.

    Args:
        obj: Dictionary or list to access
        *keys: Keys/indices to traverse
        default: Default value if path doesn't exist

    Returns:
        Value at path or default
    """
    current = obj

    for key in keys:
        try:
            current = current[key]
        except (KeyError, IndexError, TypeError):
            return default

    return current


def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove None values from a dictionary.

    Args:
        d: Dictionary to clean

    Returns:
        Dictionary without None values
    """
    return {k: v for k, v in d.items() if v is not None}


def first_non_none(*values: Any) -> Any:
    """
    Return the first non-None value.

    Args:
        *values: Values to check

    Returns:
        First non-None value or None
    """
    for value in values:
        if value is not None:
            return value
    return None


def generate_id(prefix: str = "", length: int = 8) -> str:
    """
    Generate a random ID.

    Args:
        prefix: ID prefix
        length: Length of random part

    Returns:
        Generated ID
    """
    import random
    import string

    chars = string.ascii_lowercase + string.digits
    random_part = "".join(random.choices(chars, k=length))

    return f"{prefix}{random_part}" if prefix else random_part
