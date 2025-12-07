# Product Description

## Purpose

`iPhone Favorites Saver` is a command-line Python application that preserves photo metadata when transferring photos from iPhone to PC. It specifically migrates favorites status and image descriptions from iPhone's Photos.sqlite database into the EXIF metadata of the copied image files.

## Problem It Solves

When users copy photos from their iPhone to PC, they lose important metadata:
- **Favorites status**: Photos marked as favorites on iPhone lose this designation
- **Image descriptions**: Custom captions/descriptions written on iPhone are not transferred
- **Organizational context**: Without this metadata, users lose their photo organization system

This tool bridges that gap by:
1. Reading the original metadata from iPhone's Photos.sqlite database
2. Writing that metadata into standard EXIF fields that are portable and tool-independent
3. Preserving the user's photo organization workflow across platforms

## User Experience Goals

### Simplicity
- Single command execution
- Clear command-line interface
- Minimal setup required

### Safety
- Check existing EXIF data before overwriting
- Prompt user for confirmation when data conflicts exist
- Non-destructive operation (reads from database, writes to EXIF)

### Transparency
- Display what data will be modified
- Show existing ratings/descriptions when present
- Clear progress indication for batch operations

## How It Works

**Prerequisites:**
- User has already copied photos from iPhone to PC
- Original folder structure and filenames are preserved
- User has access to iPhone's Photos.sqlite database file

**Workflow:**
1. User runs the command with two required inputs:
   - Path to Photos.sqlite database
   - Path to directory containing copied photos (100APPLE folders)

2. Application processes each photo:
   - Reads favorites/description from database
   - Checks if destination file already has rating/description in EXIF
   - If existing data found: prompts user to overwrite or keep
   - If no conflict: writes metadata to EXIF

3. Result: Photos on PC now contain the same organizational metadata as on iPhone

## Key Features

1. **Favorites Migration**: Maps iPhone favorites to EXIF rating field
2. **Description Migration**: Transfers photo descriptions to EXIF description field
3. **Conflict Detection**: Identifies and prompts for existing EXIF data
4. **User Control**: Interactive prompts for overwrite decisions
5. **Database Flexibility**: Accepts renamed Photos.sqlite files