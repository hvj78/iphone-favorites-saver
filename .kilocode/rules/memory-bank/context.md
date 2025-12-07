# Current Context

## Project Status
**New project - not yet implemented**

This is a greenfield Python command-line application. No code has been written yet.

## Current Focus
Memory Bank initialization - documenting the project requirements and design.

## Next Steps
1. Implement project structure:
   - Create main Python script
   - Set up requirements.txt for dependencies
   - Add README with usage instructions

2. Core functionality to implement:
   - SQLite database reader for Photos.sqlite
   - Photo file discovery (scanning for 100APPLE folders)
   - EXIF metadata reader/writer integration
   - Conflict detection logic
   - Interactive user prompts
   - Command-line argument parsing

3. Testing considerations:
   - Test with sample Photos.sqlite database
   - Verify EXIF writing on various image formats
   - Test conflict detection and user prompts

## Recent Changes
- Memory Bank initialized (just now)

## Notes
- User expects the project to work with already-copied photos, preserving original folder structure
- Database file may be renamed, so path must be flexible
- Safety is paramount - always check before overwriting existing EXIF data