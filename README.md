# iPhone Favorites Saver

A command-line Python application that migrates favorites status and image descriptions from an iPhone's Photos.sqlite database into the EXIF metadata of copied photo files.

## Problem Solved

When copying photos from iPhone to PC, important metadata like favorites status and descriptions are lost. This tool preserves that metadata by writing it to standard EXIF fields that are portable across platforms and tools.

## Prerequisites

- Python 3.8 or higher
- [exiftool](https://exiftool.org/) installed and available in PATH
- Photos copied from iPhone with original folder structure preserved
- Access to iPhone's Photos.sqlite database file

## Installation

1. Clone or download this repository
2. Ensure Python 3.8+ is installed
3. Install exiftool:
   - **Windows**: Download from [exiftool.org](https://exiftool.org/) or use `choco install exiftool`
   - **macOS**: `brew install exiftool`
   - **Linux**: `sudo apt-get install libimage-exiftool-perl` (Ubuntu/Debian) or `sudo yum install perl-Image-ExifTool` (CentOS/RHEL)

## Usage

```bash
python iphone-favorites-saver.py <path_to_Photos.sqlite> <path_to_photo_directory> [options]
```

### Arguments

- `path_to_Photos.sqlite`: Path to the iPhone's Photos.sqlite database file (may be renamed)
- `path_to_photo_directory`: Root directory containing the copied photos (should contain 100APPLE folders)

### Options

- `-v, --verbose`: Print per-file progress and diagnostic details to the console
- `--dry-run`: Show the planned EXIF updates without modifying any files
- `--overwrite-original`: Add exiftool's `-overwrite_original` flag so no `*_original` backups are kept

### Example

```bash
python iphone-favorites-saver.py /path/to/Photos.sqlite /path/to/DCIM --verbose
```

## Logging

Every run creates a timestamped file inside the `logs/` directory (e.g., `logs/iphone_favorites_saver_20250101_101500.log`).
Logs capture the CLI invocation, Python/exiftool versions, each exiftool command, and the final statistics, providing a full audit trail.

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Migration completed without errors |
| 1 | Migration finished but one or more files failed |
| 2 | `exiftool` is missing or could not be executed |
| 3 | Invalid or unreadable Photos.sqlite database |
| 4 | No supported photo files were discovered in the supplied directory |

## How It Works

1. Reads favorites status and descriptions from Photos.sqlite
2. Scans for photo files in the copied directory structure
3. For each photo:
   - Checks if EXIF already contains rating/description
   - Prompts user if conflicts exist
   - Writes metadata to EXIF fields (Rating for favorites, Description for captions)

## Safety Features

- Always checks existing EXIF data before overwriting
- Prompts for user confirmation on conflicts
- Non-destructive operation (only adds/modifies EXIF, doesn't touch database)
- Dry-run mode available for preview

## Supported Formats

- JPEG (.jpg, .jpeg)
- HEIC (.heic)
- PNG (.png)

## License

[Add license information here]

## Contributing

[Add contribution guidelines here]