# Current Context

## Project Status
**CLI implemented - undergoing polishing**

The iPhone Favorites Saver script exists as `iphone-favorites-saver.py` with argument parsing, SQLite ingestion, file scanning, EXIF read/write, logging, and conflict handling already coded.

## Current Focus
- Aligning branding/log output with the new application name
- Improving logging clarity (read vs write vs dry-run)
- Ensuring optional `--overwrite-original` flag propagates through every EXIF call

## Next Steps
1. Exercise the CLI end-to-end with sample Photos.sqlite + DCIM trees
2. Capture user feedback on the new logging format and overwrite flag defaults
3. Package usability improvements (README polish, sample commands, screenshots)

## Recent Changes
- Script renamed to `iphone-favorites-saver.py` and log files now use the `iphone_favorites_saver_*.log` prefix
- README/requirements updated to display "iPhone Favorites Saver" plus the new CLI name
- Memory Bank files refreshed to describe the renamed entry point and usage patterns

## Notes
- Default behavior keeps exiftool `_original` backups; pass `--overwrite-original` to suppress them
- Safety-first flow is preserved: read before write, prompt on conflicts, respect dry-run mode
- Expect future enhancements (e.g., better progress UI) once the rename dust settles
