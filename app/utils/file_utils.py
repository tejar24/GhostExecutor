"""
File Utility Functions

Provides common file operations for the Ghost-QC application.
"""

import glob
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Union


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Directory path to ensure exists

    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def read_file(
    path: Union[str, Path],
    encoding: str = "utf-8",
    default: Optional[str] = None,
) -> Optional[str]:
    """
    Read content from a file.

    Args:
        path: File path to read
        encoding: File encoding (default: utf-8)
        default: Default value if file doesn't exist

    Returns:
        File content or default value
    """
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        return default
    except Exception as e:
        raise IOError(f"Failed to read file {path}: {e}")


def write_file(
    path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    create_dirs: bool = True,
) -> Path:
    """
    Write content to a file.

    Args:
        path: File path to write
        content: Content to write
        encoding: File encoding (default: utf-8)
        create_dirs: Create parent directories if needed

    Returns:
        Path object for the written file
    """
    file_path = Path(path)

    if create_dirs:
        file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)

    return file_path


def find_files(
    pattern: str,
    root_dir: Optional[Union[str, Path]] = None,
    recursive: bool = True,
) -> List[Path]:
    """
    Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.feature", "**/*.py")
        root_dir: Root directory to search in (default: current directory)
        recursive: Enable recursive search with **

    Returns:
        List of matching file paths
    """
    if root_dir:
        pattern = str(Path(root_dir) / pattern)

    return [Path(p) for p in glob.glob(pattern, recursive=recursive)]


def get_timestamp_filename(
    prefix: str,
    extension: str,
    directory: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Generate a timestamped filename.

    Args:
        prefix: Filename prefix
        extension: File extension (without dot)
        directory: Output directory (optional)

    Returns:
        Path with timestamped filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.{extension}"

    if directory:
        return Path(directory) / filename
    return Path(filename)


def copy_file(
    src: Union[str, Path],
    dst: Union[str, Path],
    overwrite: bool = False,
) -> Path:
    """
    Copy a file to a new location.

    Args:
        src: Source file path
        dst: Destination file path
        overwrite: Whether to overwrite existing file

    Returns:
        Path to the copied file
    """
    src_path = Path(src)
    dst_path = Path(dst)

    if dst_path.exists() and not overwrite:
        raise FileExistsError(f"Destination file already exists: {dst_path}")

    dst_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_path, dst_path)

    return dst_path


def delete_file(path: Union[str, Path], ignore_missing: bool = True) -> bool:
    """
    Delete a file.

    Args:
        path: File path to delete
        ignore_missing: Don't raise error if file doesn't exist

    Returns:
        True if file was deleted, False if it didn't exist
    """
    file_path = Path(path)

    if not file_path.exists():
        if ignore_missing:
            return False
        raise FileNotFoundError(f"File not found: {file_path}")

    file_path.unlink()
    return True


def get_file_size(path: Union[str, Path]) -> int:
    """
    Get file size in bytes.

    Args:
        path: File path

    Returns:
        File size in bytes
    """
    return Path(path).stat().st_size


def get_file_modified_time(path: Union[str, Path]) -> datetime:
    """
    Get file modification time.

    Args:
        path: File path

    Returns:
        Modification datetime
    """
    return datetime.fromtimestamp(Path(path).stat().st_mtime)


def clean_directory(
    path: Union[str, Path],
    pattern: str = "*",
    older_than_days: Optional[int] = None,
) -> int:
    """
    Clean files from a directory.

    Args:
        path: Directory path
        pattern: Glob pattern for files to delete
        older_than_days: Only delete files older than this many days

    Returns:
        Number of files deleted
    """
    dir_path = Path(path)
    if not dir_path.exists():
        return 0

    deleted_count = 0
    cutoff_time = None

    if older_than_days is not None:
        from datetime import timedelta
        cutoff_time = datetime.now() - timedelta(days=older_than_days)

    for file_path in dir_path.glob(pattern):
        if file_path.is_file():
            if cutoff_time:
                file_time = get_file_modified_time(file_path)
                if file_time >= cutoff_time:
                    continue

            file_path.unlink()
            deleted_count += 1

    return deleted_count


def get_relative_path(
    path: Union[str, Path],
    base: Optional[Union[str, Path]] = None,
) -> Path:
    """
    Get path relative to a base directory.

    Args:
        path: Full path
        base: Base directory (default: current working directory)

    Returns:
        Relative path
    """
    full_path = Path(path).resolve()
    base_path = Path(base).resolve() if base else Path.cwd()

    try:
        return full_path.relative_to(base_path)
    except ValueError:
        return full_path
