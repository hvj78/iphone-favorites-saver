# iPhone Favorites Saver

A command-line Python application that migrates favorites status and image descriptions from an iPhone's Photos.sqlite database into the EXIF metadata of copied photo files.

## Problem Solved

When copying photos from iPhone to PC, important metadata like favorites status and descriptions are lost. This tool preserves that metadata by writing it to standard EXIF fields that are portable across platforms and tools.

I personally use Adobe Lightroom Classic for many-many years and started using the favorites on iPhone only lately, so I realized this problem just this year, that favorites and image descriptions are not stored in the HEIC and other image files.
Using this script, the data is read from the Photos.sqlite database and written into the image files!
You have to read the metadata from the files in Lightroom: right click on all selected images in grid view and select Metadata->Read metadata from files.

Lightroom users, important!

Before using this script, make sure, that all your metadata is already saved into the image files (or their xmp sidecars)! As you must read the metadata from the files after the script ran successfully and you do not want to lose all your precious metadata!

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

- `-v, --verbose`: Print per-file progress, dry-run command previews, and additional diagnostics
- `--dry-run`: Show the planned EXIF updates without modifying any files
- `--overwrite-original`: Add exiftool's `-overwrite_original` flag so no `*_original` backups are kept

### Example

```bash
python iphone-favorites-saver.py /path/to/Photos.sqlite /path/to/DCIM --verbose
```

## Logging

Every run creates a timestamped file inside the `logs/` directory (e.g., `logs/iphone_favorites_saver_20250101_101500.log`).
Logs capture the CLI invocation, Python/exiftool versions, each exiftool command, and the final statistics, providing a full audit trail.

## Console Output

- **Default mode** prints only essential information (warnings/errors and the final summary) to keep output quiet.
- **Verbose mode (`-v`)** adds phase banners, per-file progress, dry-run command previews, duplicate warnings, and other diagnostics for deep insight.

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | Migration completed without errors |
| 1 | Migration finished but one or more files failed |
| 2 | `exiftool` is missing or could not be executed |
| 3 | Invalid or unreadable Photos.sqlite database |
| 4 | No supported photo files were discovered in the supplied directory |

## How It Works

1. Reads favorites status and descriptions from Photos.sqlite (preferring the iOS 18 `ZASSETDESCRIPTION.ZLONGDESCRIPTION` field, with fallbacks for older schema)
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

Feel free to drop me an email to horvath.varga.janos@gmail.com
Any suggestions, PRs welcomed!

## AI coding background

I crafted the concept using kilo-code with Claude Sonnet 4.5, done the first implementation with Grok Code fast 1 (just to try that model out, worked really fast and it was OK, but was unable to do fixes and minor changes).
I did the iterations using GPT-5.1-Codex but was weak in several, even simple cases and burned my tokens via openrouter.
I tried to reverse engineer the Photos.sqlite using kilo-code with Sonnet 4.5, but it simply failed.
So finally I installed Claude Code and that worked like a magic using Opus 4.5 model!
(I personally did not wrote any single line of code in this repo, all characters were generated with above AI models! I wrote only these lines here in README.md manually and prompted the system and made the manual testing)
