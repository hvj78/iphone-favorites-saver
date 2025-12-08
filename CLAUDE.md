# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

iPhone Favorites Saver is a command-line Python tool that migrates favorites status and image descriptions from an iPhone's Photos.sqlite database into EXIF metadata of copied photo files.

## Running the Application

```bash
python iphone-favorites-saver.py <path_to_Photos.sqlite> <path_to_photo_directory> [options]
```

Options:
- `-v, --verbose`: Enable verbose output
- `--dry-run`: Preview changes without modifying files
- `--overwrite-original`: Skip creating backup files

## External Dependencies

- **Python 3.8+** (uses only standard library)
- **exiftool** must be installed and in PATH (https://exiftool.org/)

No pip dependencies are required.

## Architecture

The application is a single-file script (`iphone-favorites-saver.py`) following a pipeline pattern:

1. **Database Reader**: Reads Photos.sqlite, queries ZASSET table for favorites/descriptions. Handles iOS version differences via dynamic schema detection (ZASSETDESCRIPTION, ZADDITIONALASSETATTRIBUTES, ZEXTENDEDATTRIBUTES).

2. **File Scanner**: Walks photo directory looking for `*/[0-9]+APPLE/*` folders. Matches database entries to files using normalized paths.

3. **EXIF Handler**: Uses subprocess calls to exiftool for reading/writing metadata. Maps favorites to `Rating` field (value 4), descriptions to `ImageDescription` and `Description` fields.

4. **Conflict Resolution**: Prompts user when existing EXIF data would be overwritten. Supports per-file decisions or "skip all" for batch operations.

## Key Data Structures

- `PhotoMeta`: Database metadata (relative_path, favorite, description)
- `FileRecord`: Discovered file on disk (rel_path, full_path)
- `MatchedPhoto`: Pairing of database metadata with discovered file
- `ExifData`: Existing EXIF values (rating, description)

## Exit Codes

- 0: Success
- 1: Migration completed with errors
- 2: exiftool missing
- 3: Invalid database
- 4: No photo files found

## Logging

Logs are written to `logs/iphone_favorites_saver_YYYYMMDD_HHMMSS.log` with full audit trail of all exiftool commands.
