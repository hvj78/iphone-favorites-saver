#!/usr/bin/env python3
"""iPhone Favorites Saver - migrate favorites and descriptions to EXIF metadata."""

from __future__ import annotations

import argparse
import logging
import os
import shlex
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

MIN_PYTHON = (3, 8)
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".png"}
APPLE_SUFFIX = "APPLE"

EXIT_SUCCESS = 0
EXIT_GENERAL_ERROR = 1
EXIT_EXIFTOOL_MISSING = 2
EXIT_INVALID_DB = 3
EXIT_NO_PHOTOS = 4


@dataclass(frozen=True)
class PhotoMeta:
    """Metadata extracted from Photos.sqlite for a single asset."""

    relative_path: str
    favorite: bool
    description: str


@dataclass(frozen=True)
class FileRecord:
    """Represents a discovered file on disk."""

    rel_path: str
    full_path: str


@dataclass(frozen=True)
class MatchedPhoto:
    """Pairing of database metadata with a discovered file."""

    record: FileRecord
    meta: PhotoMeta


@dataclass
class ExifData:
    """Existing EXIF values for a photo."""

    rating: Optional[int]
    description: Optional[str]


class ExifToolError(RuntimeError):
    """Raised when exiftool execution fails."""


class ConsoleReporter:
    """Handles stdout messaging with optional verbosity."""

    def __init__(self, verbose: bool) -> None:
        self.verbose = verbose

    def phase(self, message: str) -> None:
        if self.verbose:
            print(f"\n== {message} ==")

    def info(self, message: str, *, verbose_only: bool = False) -> None:
        if verbose_only and not self.verbose:
            return
        print(message)

    def warn(self, message: str) -> None:
        print(f"WARNING: {message}")

    def error(self, message: str) -> None:
        print(f"ERROR: {message}")

    def detail(self, message: str) -> None:
        if self.verbose:
            print(message)


def strip_arg_quotes(value: str) -> str:
    return value.strip().strip('"')


def cleanup_path_arg(value: str) -> Tuple[str, bool]:
    cleaned = strip_arg_quotes(value)
    verbose_found = False
    for flag in (" -v", " --verbose"):
        if cleaned.endswith(flag):
            cleaned = cleaned[: -len(flag)]
            verbose_found = True
            break
    return cleaned.strip(), verbose_found


def main() -> None:
    ensure_python_version()
    args = parse_args()

    args.database = strip_arg_quotes(args.database)
    cleaned_photo_dir, verbose_from_path = cleanup_path_arg(args.photo_dir)
    args.photo_dir = cleaned_photo_dir
    if verbose_from_path:
        args.verbose = True

    start_time = time.time()
    reporter = ConsoleReporter(args.verbose)

    logger, log_path = setup_logger()
    reporter.phase("Checking dependencies")
    try:
        exiftool_info = check_dependencies()
    except FileNotFoundError:
        message = "exiftool not found. Install it from https://exiftool.org/ before running."
        logger.error(message)
        reporter.error(message)
        sys.exit(EXIT_EXIFTOOL_MISSING)
    except subprocess.CalledProcessError as exc:
        logger.error("Failed to execute exiftool -ver: %s", exc)
        reporter.error("Failed to execute exiftool -ver. See log for details.")
        sys.exit(EXIT_EXIFTOOL_MISSING)

    log_run_header(logger, args, exiftool_info, log_path)

    reporter.phase("Validating database")
    if not validate_database(args.database, logger, reporter):
        sys.exit(EXIT_INVALID_DB)

    reporter.phase("Reading metadata from Photos.sqlite")
    metadata = read_database_metadata(args.database, logger)
    if not metadata:
        reporter.warn("Database contains no favorites or descriptions. Nothing to migrate.")
        logger.warning("Database query returned zero rows containing favorites/descriptions.")

    reporter.phase("Scanning photo library")
    photo_files = scan_photo_files(args.photo_dir, logger, reporter)
    if not photo_files:
        logger.error("No supported photo files found under %s", args.photo_dir)
        reporter.error(f"No supported photo files found under {args.photo_dir}")
        sys.exit(EXIT_NO_PHOTOS)

    reporter.phase("Matching metadata to files")
    matched = match_metadata(metadata, photo_files, logger, reporter)
    if not matched:
        reporter.info("No photo files matched the database entries. Exiting.")
        logger.warning("No matches between database metadata and scanned files.")
        log_run_footer(logger, {"processed": 0, "skipped": 0, "errors": 0}, start_time)
        sys.exit(EXIT_SUCCESS)

    reporter.phase(f"Migrating metadata for {len(matched)} photo(s)")
    stats = run_migration(matched, args, logger, reporter)

    log_run_footer(logger, stats, start_time)

    reporter.phase("Migration complete")
    reporter.info(
        f"Processed: {stats['processed']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}"
    )

    exit_code = EXIT_SUCCESS if stats["errors"] == 0 else EXIT_GENERAL_ERROR
    sys.exit(exit_code)


def ensure_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        min_version = ".".join(str(v) for v in MIN_PYTHON)
        raise SystemExit(
            f"Python {min_version}+ is required. Current version: {sys.version.split()[0]}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate iPhone photo favorites and descriptions to EXIF metadata"
    )
    parser.add_argument("database", help="Path to Photos.sqlite database file")
    parser.add_argument(
        "photo_dir",
        help="Root directory containing copied photos (with 100APPLE/101APPLE/etc. folders)",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show actions without writing EXIF data"
    )
    parser.add_argument(
        "--overwrite-original",
        action="store_true",
        help="Pass -overwrite_original to exiftool so no *_original backups are kept",
    )
    return parser.parse_args()


def setup_logger() -> Tuple[logging.Logger, Path]:
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"iphone_favorites_saver_{timestamp}.log"

    logger = logging.getLogger("migrator")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger, log_path


def log_run_header(
    logger: logging.Logger, args: argparse.Namespace, exiftool_info: Tuple[str, str], log_path: Path
) -> None:
    cmd_line = "python " + " ".join(shlex.quote(os.fspath(arg)) for arg in sys.argv[1:])
    logger.info("=== Migration started ===")
    logger.info("Log file: %s", log_path)
    logger.info("CLI invocation: %s", cmd_line)
    logger.info("Python version: %s", sys.version.replace("\n", " "))
    logger.info("exiftool path: %s", exiftool_info[0])
    logger.info("exiftool version: %s", exiftool_info[1])


def log_run_footer(logger: logging.Logger, stats: Dict[str, int], start_time: float) -> None:
    duration = time.time() - start_time
    logger.info("=== Migration finished ===")
    logger.info(
        "Summary -> processed: %s, skipped: %s, errors: %s",
        stats.get("processed", 0),
        stats.get("skipped", 0),
        stats.get("errors", 0),
    )
    logger.info("Runtime: %.2f seconds", duration)


def check_dependencies() -> Tuple[str, str]:
    exiftool_path = shutil.which("exiftool")
    if not exiftool_path:
        raise FileNotFoundError("exiftool not found in PATH")

    result = subprocess.run(
        [exiftool_path, "-ver"], capture_output=True, text=True, check=True
    )
    version = result.stdout.strip()
    return exiftool_path, version


def validate_database(
    db_path: str, logger: logging.Logger, reporter: ConsoleReporter
) -> bool:
    if not os.path.exists(db_path):
        msg = f"Database file not found: {db_path}"
        logger.error(msg)
        reporter.error(msg)
        return False

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}

        if "ZASSET" not in tables:
            msg = f"Not a valid Photos.sqlite database (missing ZASSET): {db_path}"
            logger.error(msg)
            reporter.error(msg)
            return False
    except sqlite3.Error as exc:
        msg = f"Failed to open database {db_path}: {exc}"
        logger.error(msg)
        reporter.error("Failed to open database. See log for details.")
        return False

    return True


def read_database_metadata(db_path: str, logger: logging.Logger) -> Dict[str, PhotoMeta]:
    metadata: Dict[str, PhotoMeta] = {}

    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            tables = fetch_table_names(cursor)
            query, desc_expr = build_metadata_query(cursor, tables)

            cursor.execute(query)
            rows = cursor.fetchall()

    except sqlite3.Error as exc:
        logger.error("Error reading database %s: %s", db_path, exc)
        return {}

    duplicates = 0
    for row in rows:
        filename_db = row["ZFILENAME"] or ""
        directory = row["ZDIRECTORY"] or ""
        favorite = bool(row["ZFAVORITE"])
        description = (row["DESCRIPTION"] or "").strip()

        full_relative = build_relative_path(directory, filename_db)
        truncated = truncate_to_apple_path(full_relative)
        normalized = normalize_rel_path(truncated)

        if normalized in metadata:
            duplicates += 1
            continue

        metadata[normalized] = PhotoMeta(truncated, favorite, description)

    logger.info(
        "Loaded %s metadata row(s) (duplicates skipped: %s). Description expression: %s",
        len(metadata),
        duplicates,
        desc_expr,
    )
    return metadata


def fetch_table_names(cursor: sqlite3.Cursor) -> Dict[str, List[str]]:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    table_columns: Dict[str, List[str]] = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        table_columns[table] = columns
    return table_columns


def build_metadata_query(cursor: sqlite3.Cursor, tables: Dict[str, List[str]]) -> Tuple[str, str]:
    joins: List[str] = []
    desc_clauses: List[str] = []

    # Determine if this is iOS 18+ schema (uses ZADDITIONALATTRIBUTES) or older (uses Z_PK = ZASSET)
    zasset_cols = tables.get("ZASSET", [])
    is_ios18 = "ZADDITIONALATTRIBUTES" in zasset_cols

    # First join: ZASSET -> ZADDITIONALASSETATTRIBUTES
    if "ZADDITIONALASSETATTRIBUTES" in tables:
        if is_ios18:
            # iOS 18: ZASSET.ZADDITIONALATTRIBUTES -> ZADDITIONALASSETATTRIBUTES.Z_PK
            joins.append(
                "LEFT JOIN ZADDITIONALASSETATTRIBUTES ON ZASSET.ZADDITIONALATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK"
            )
        else:
            # Older iOS: ZASSET.Z_PK -> ZADDITIONALASSETATTRIBUTES.ZASSET
            joins.append(
                "LEFT JOIN ZADDITIONALASSETATTRIBUTES ON ZASSET.Z_PK = ZADDITIONALASSETATTRIBUTES.ZASSET"
            )

        if "ZTITLE" in tables["ZADDITIONALASSETATTRIBUTES"]:
            desc_clauses.append("NULLIF(ZADDITIONALASSETATTRIBUTES.ZTITLE, '')")

    # Second join: ZADDITIONALASSETATTRIBUTES -> ZASSETDESCRIPTION
    if (
        "ZASSETDESCRIPTION" in tables
        and "ZADDITIONALASSETATTRIBUTES" in tables
    ):
        aaa_cols = tables.get("ZADDITIONALASSETATTRIBUTES", [])
        desc_cols = tables.get("ZASSETDESCRIPTION", [])

        if "ZASSETDESCRIPTION" in aaa_cols:
            # iOS 18: ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION -> ZASSETDESCRIPTION.Z_PK
            joins.append(
                "LEFT JOIN ZASSETDESCRIPTION ON ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION = ZASSETDESCRIPTION.Z_PK"
            )
        elif "ZASSETATTRIBUTES" in desc_cols:
            # Older iOS: ZASSETDESCRIPTION.ZASSETATTRIBUTES -> ZADDITIONALASSETATTRIBUTES.Z_PK
            joins.append(
                "LEFT JOIN ZASSETDESCRIPTION ON ZASSETDESCRIPTION.ZASSETATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK"
            )

        if "ZLONGDESCRIPTION" in tables["ZASSETDESCRIPTION"]:
            desc_clauses.insert(0, "NULLIF(ZASSETDESCRIPTION.ZLONGDESCRIPTION, '')")

    # Third join: ZEXTENDEDATTRIBUTES (for older iOS versions with ZCAPTION)
    if "ZEXTENDEDATTRIBUTES" in tables and "ZCAPTION" in tables["ZEXTENDEDATTRIBUTES"]:
        joins.append(
            "LEFT JOIN ZEXTENDEDATTRIBUTES ON ZASSET.Z_PK = ZEXTENDEDATTRIBUTES.ZASSET"
        )
        desc_clauses.append("NULLIF(ZEXTENDEDATTRIBUTES.ZCAPTION, '')")

    if desc_clauses:
        desc_expr = f"COALESCE({', '.join(desc_clauses)}, '')"
    else:
        desc_expr = "''"

    query = f"""
        SELECT
            ZASSET.ZFILENAME,
            ZASSET.ZDIRECTORY,
            ZASSET.ZFAVORITE,
            {desc_expr} AS DESCRIPTION
        FROM ZASSET
        {' '.join(joins)}
        WHERE ZASSET.ZTRASHEDSTATE = 0
          AND (ZASSET.ZFAVORITE = 1 OR {desc_expr} != '')
    """

    return " ".join(query.split()), desc_expr


def build_relative_path(directory: str, filename: str) -> str:
    if not directory:
        return filename
    combined = Path(directory) / filename
    return combined.as_posix()


def truncate_to_apple_path(path_str: str) -> str:
    parts = path_str.replace("\\", "/").split("/")
    for idx, part in enumerate(parts):
        if part.upper().endswith(APPLE_SUFFIX) and part[:-5].isdigit():
            return "/".join(parts[idx:])
    return path_str.replace("\\", "/")


def normalize_rel_path(rel_path: str) -> str:
    return Path(rel_path).as_posix().lower()


def scan_photo_files(
    photo_dir: str, logger: logging.Logger, reporter: ConsoleReporter
) -> Dict[str, FileRecord]:
    base_path = Path(photo_dir)
    if not base_path.exists():
        logger.error("Photo directory not found: %s", photo_dir)
        reporter.error(f"Photo directory not found: {photo_dir}")
        return {}

    photo_files: Dict[str, FileRecord] = {}
    apple_dir_found = False

    for root, _, files in os.walk(base_path):
        root_path = Path(root)
        path_parts = [part for part in root_path.relative_to(base_path).parts if part]
        if any(part.upper().endswith(APPLE_SUFFIX) and part[:-5].isdigit() for part in path_parts):
            apple_dir_found = True
        else:
            continue

        for file_name in files:
            ext = Path(file_name).suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue
            rel_path = (root_path / file_name).relative_to(base_path).as_posix()
            normalized = normalize_rel_path(rel_path)
            if normalized in photo_files:
                logger.warning("Duplicate file encountered after normalization: %s", rel_path)
                reporter.detail(f"Duplicate file skipped: {rel_path}")
                continue
            photo_files[normalized] = FileRecord(rel_path, str(root_path / file_name))

    if not apple_dir_found:
        message = f"No folders matching */[0-9]+APPLE were found under {photo_dir}"
        logger.warning(message)
        reporter.warn(message)

    logger.info("Discovered %s photo file(s) under %s", len(photo_files), photo_dir)
    reporter.info(f"Discovered {len(photo_files)} supported photo file(s)")
    return photo_files


def match_metadata(
    metadata: Dict[str, PhotoMeta],
    photo_files: Dict[str, FileRecord],
    logger: logging.Logger,
    reporter: ConsoleReporter,
) -> List[MatchedPhoto]:
    matched: List[MatchedPhoto] = []
    missing_files = 0
    for key, meta in metadata.items():
        file_record = photo_files.get(key)
        if not file_record:
            missing_files += 1
            continue
        matched.append(MatchedPhoto(file_record, meta))

    if missing_files:
        message = f"{missing_files} metadata record(s) did not have matching files on disk."
        logger.warning(message)
        reporter.warn(message)

    logger.info("Matched %s file(s) between database and disk.", len(matched))
    reporter.info(f"Matched {len(matched)} photo(s)")
    return matched


def run_migration(
    matched: Sequence[MatchedPhoto],
    args: argparse.Namespace,
    logger: logging.Logger,
    reporter: ConsoleReporter,
) -> Dict[str, int]:
    stats = {"processed": 0, "skipped": 0, "errors": 0}
    skip_all_conflicts = False

    for entry in matched:
        rel_path = entry.record.rel_path
        meta = entry.meta
        full_path = entry.record.full_path

        reporter.detail(f"Processing {rel_path}")

        if not meta.favorite and not meta.description:
            stats["skipped"] += 1
            reporter.detail(f"Skipping {rel_path} - no metadata present in database.")
            continue

        try:
            existing = read_exif_data(full_path, logger)
        except ExifToolError:
            reporter.error(f"Failed to read EXIF for {rel_path}. See log for details.")
            stats["errors"] += 1
            continue

        needs_rating = meta.favorite and (existing.rating is None or existing.rating < 4)
        needs_description = bool(meta.description) and meta.description != (existing.description or "")

        if not needs_rating and not needs_description:
            logger.info("Skipping %s - no EXIF changes required.", rel_path)
            reporter.detail(f"Skipping {rel_path} - already up to date.")
            stats["skipped"] += 1
            continue

        has_conflict = evaluate_conflict(existing, needs_rating, needs_description)
        if has_conflict:
            if skip_all_conflicts:
                stats["skipped"] += 1
                reporter.detail(f"Skipping {rel_path} due to 'skip all' selection.")
                continue

            decision = prompt_conflict(rel_path, existing, meta)
            if decision == "skip":
                stats["skipped"] += 1
                reporter.detail(f"User chose to keep existing metadata for {rel_path}.")
                continue
            if decision == "skip_all":
                skip_all_conflicts = True
                stats["skipped"] += 1
                reporter.detail("User chose to skip all remaining conflicts.")
                continue
            # decision == "overwrite" -> continue

        action_rating = 4 if needs_rating else None
        action_description = meta.description if needs_description else None

        if args.dry_run:
            reporter.detail(
                f"[DRY RUN] Would update {rel_path}: rating={action_rating}, "
                f"description={'<unchanged>' if action_description is None else repr(action_description)}"
            )
            cmd_args = build_write_cmd_args(
                full_path, action_rating, action_description, args.overwrite_original
            )
            if cmd_args:
                logger.info(
                    "DRY RUN - would run: %s",
                    format_command(["exiftool", "-charset", "utf8", "-q", "-q", *cmd_args]),
                )
            stats["processed"] += 1
            continue

        try:
            success = write_exif_data(
                full_path,
                action_rating,
                action_description,
                args.overwrite_original,
                logger,
            )
        except ExifToolError:
            success = False

        if success:
            reporter.detail(f"Updated {rel_path}")
            stats["processed"] += 1
        else:
            reporter.error(f"Failed to update {rel_path}. See log for details.")
            stats["errors"] += 1

    return stats


def evaluate_conflict(existing: ExifData, needs_rating: bool, needs_description: bool) -> bool:
    rating_conflict = needs_rating and existing.rating is not None and existing.rating != 4
    description_conflict = needs_description and bool(existing.description)
    return rating_conflict or description_conflict


def prompt_conflict(rel_path: str, existing: ExifData, meta: PhotoMeta) -> str:
    print(f"\nConflict detected for {rel_path}:")
    print(
        f"  Existing -> rating={existing.rating}, description={repr(existing.description) if existing.description else '<empty>'}"
    )
    target_desc = meta.description if meta.description else "<empty>"
    print(
        f"  Incoming -> rating={'4 (favorite)' if meta.favorite else '<unchanged>'}, description={repr(target_desc)}"
    )

    while True:
        response = (
            input("Overwrite (y), keep existing (n), or skip all future conflicts (s)? ")
            .strip()
            .lower()
        )
        if response in {"y", "n", "s"}:
            break
        print("Please enter 'y', 'n', or 's'.")

    if response == "y":
        return "overwrite"
    if response == "s":
        return "skip_all"
    return "skip"


def read_exif_data(file_path: str, logger: logging.Logger) -> ExifData:
    args = ["-Rating", "-ImageDescription", "-Description", file_path]
    result = run_exiftool(args, logger, purpose="read")
    rating: Optional[int] = None
    description: Optional[str] = None

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        key, _, value = line.partition(":")
        key = key.strip().lower()
        value = value.strip()
        if key == "rating":
            try:
                rating = int(value)
            except ValueError:
                continue
        elif key in {"imagedescription", "description"}:
            if value:
                description = value

    return ExifData(rating, description)


def write_exif_data(
    file_path: str,
    rating: Optional[int],
    description: Optional[str],
    overwrite_original: bool,
    logger: logging.Logger,
) -> bool:
    if rating is None and description is None:
        return True

    cmd_args = build_write_cmd_args(file_path, rating, description, overwrite_original)
    if not cmd_args:
        return True

    run_exiftool(cmd_args, logger, purpose="write")
    return True


def build_write_cmd_args(
    file_path: str,
    rating: Optional[int],
    description: Optional[str],
    overwrite_original: bool,
) -> Optional[List[str]]:
    updates: List[str] = []
    if rating is not None:
        updates.append(f"-Rating={rating}")
    if description is not None:
        updates.extend(
            [
                f"-ImageDescription={description}",
                f"-Description={description}",
            ]
        )

    if not updates:
        return None

    cmd: List[str] = []
    if overwrite_original:
        cmd.append("-overwrite_original")
    cmd.extend(updates)
    cmd.append(file_path)
    return cmd


def run_exiftool(
    cmd_args: Sequence[str], logger: logging.Logger, purpose: str = "RUN"
) -> subprocess.CompletedProcess[str]:
    full_cmd = ["exiftool", "-charset", "utf8", "-q", "-q", *cmd_args]
    display_cmd = format_command(full_cmd)
    logger.info("[%s] exiftool command: %s", purpose.upper(), display_cmd)

    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, check=True)
        return result
    except subprocess.CalledProcessError as exc:
        stdout = exc.stdout.strip()
        stderr = exc.stderr.strip()
        logger.error(
            "exiftool command failed\nCommand: %s\nReturn code: %s\nSTDOUT:%s\nSTDERR:%s",
            display_cmd,
            exc.returncode,
            f"\n{stdout}" if stdout else " <empty>",
            f"\n{stderr}" if stderr else " <empty>",
        )
        raise ExifToolError(display_cmd) from exc


def format_command(parts: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in parts)


if __name__ == "__main__":
    main()
