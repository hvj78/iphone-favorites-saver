# Technology Stack

## Core Technologies

### Python 3.x
**Minimum Version**: Python 3.6+ (for f-strings and modern features)
**Recommended**: Python 3.8+

**Why Python**:
- Built-in SQLite support (no external DB driver needed)
- Excellent subprocess management for calling exiftool
- Cross-platform compatibility
- Simple deployment (single script or small package)

### SQLite3
**Module**: Built-in `sqlite3` module
**Usage**: Reading iPhone's Photos.sqlite database

**Key Considerations**:
- Read-only access to database (no writes)
- Database schema varies by iOS version
- Need to handle schema variations gracefully
- Common tables: ZASSET, ZADDITIONALASSETATTRIBUTES, ZEXTENDEDATTRIBUTES

### exiftool
**Type**: External command-line tool (not a Python library)
**Installation Required**: Yes (user must install separately)
**Platforms**: 
- Windows: Download from official site or use Chocolatey
- macOS: `brew install exiftool`
- Linux: `apt-get install libimage-exiftool-perl` or similar

**Why exiftool**:
- Industry-standard EXIF manipulation tool
- Supports all image formats (JPEG, HEIC, PNG, etc.)
- Handles metadata writing safely
- Cross-platform and well-maintained

**Usage Pattern**:
```python
import subprocess

# Check if exiftool is installed
subprocess.run(['exiftool', '-ver'], capture_output=True, check=True)

# Read EXIF data
subprocess.run(['exiftool', '-Rating', '-Description', 'photo.jpg'])

# Write EXIF data
subprocess.run(['exiftool', '-Rating=5', '-overwrite_original', 'photo.jpg'])
```

## Python Libraries

### Standard Library (No Installation Required)
- `sqlite3` - Database access
- `subprocess` - Execute exiftool commands
- `os` / `os.path` - File system operations
- `argparse` - Command-line argument parsing
- `pathlib` - Modern path handling (Python 3.4+)
- `sys` - System operations and exit codes

### Optional Third-Party Libraries
Consider these if needed:
- `PyExifTool` - Python wrapper for exiftool (simplifies subprocess calls)
- `tqdm` - Progress bars for batch operations
- `click` or `typer` - Enhanced CLI framework (overkill for this simple project)

**Current Decision**: Start with standard library only, add dependencies only if needed.

## Development Setup

### Required Tools
1. Python 3.6+ installed
2. exiftool installed and in PATH
3. Text editor or IDE (VS Code, PyCharm, etc.)
4. Git for version control

### Project Dependencies
**requirements.txt** (if using third-party libraries):
```txt
# Optional: PyExifTool wrapper
# PyExifTool==0.5.0

# Optional: Progress bars
# tqdm==4.66.0
```

### Development Workflow
1. Clone repository
2. Ensure Python 3.6+ is installed
3. Install exiftool
4. Run script directly: `python iphone-favorites-saver.py --help`
5. No virtual environment strictly needed (no dependencies initially)

## Technical Constraints

### Platform-Specific Considerations

**Windows**:
- Path separators: handles both `/` and `\`
- exiftool must be in PATH or specify full path
- Case-insensitive file systems
- Command-line encoding: UTF-8 support needed

**macOS**:
- Native platform for iPhone Photos.sqlite
- exiftool typically available via Homebrew
- HEIC format common (ensure exiftool handles it)

**Linux**:
- Photos.sqlite must be copied from iPhone/backup
- exiftool available in package managers
- File permissions considerations

### File Format Support
Application should handle:
- JPEG (.jpg, .jpeg)
- HEIC (.heic) - iPhone's native format since iOS 11
- PNG (.png)
- Possibly: RAW formats if iPhone Pro users shoot RAW

### Database Schema Variations
iPhone Photos.sqlite schema changes between iOS versions:
- iOS 14-17: Different table structures
- Need to query schema dynamically or handle multiple patterns
- Fallback gracefully if expected tables/columns missing

### Performance Constraints
- SQLite database: Can be 100MB+ for large libraries
- File scanning: Thousands of photos possible
- EXIF writes: I/O bound, ~ 1 file per second typical
- Progress indication important for user feedback

## Command-Line Interface

### Argument Parsing
Use `argparse` for:
```python
import argparse

parser = argparse.ArgumentParser(
    description='Migrate iPhone photo favorites and descriptions to EXIF'
)
parser.add_argument(
    'database',
    help='Path to Photos.sqlite database file'
)
parser.add_argument(
    'photo_dir',
    help='Root directory containing copied photos (with 100APPLE folders)'
)
parser.add_argument(
    '-v', '--verbose',
    action='store_true',
    help='Verbose output'
)
parser.add_argument(
    '--dry-run',
    action='store_true',
    help='Show what would be done without making changes'
)
```

### Exit Codes
- 0: Success
- 1: General error
- 2: Missing exiftool
- 3: Invalid database
- 4: No photos found

## Error Handling Patterns

### Check exiftool availability
```python
def check_exiftool():
    try:
        result = subprocess.run(
            ['exiftool', '-ver'],
            capture_output=True,
            text=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: exiftool not found. Please install it first.")
        return False
```

### Database validation
```python
def validate_database(db_path):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # Check if core tables exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}
        conn.close()
        
        if 'ZASSET' not in tables:
            raise ValueError("Not a valid Photos.sqlite database")
    except sqlite3.Error as e:
        raise ValueError(f"Invalid SQLite database: {e}")
```

## Testing Strategy

### Manual Testing Requirements
1. Create test Photos.sqlite database (from iPhone backup)
2. Copy sample photos with known favorites/descriptions
3. Test conflict detection with pre-existing EXIF
4. Verify EXIF tags written correctly
5. Test with various iOS versions if possible

### Edge Cases to Test
- Renamed database file
- Photos without favorites or descriptions
- Files referenced in database but missing from disk
- Images with existing EXIF rating/description
- Large photo libraries (1000+ photos)
- Special characters in descriptions
- Various image formats (JPEG, HEIC, PNG)

## Deployment

### Distribution Options
1. **Single Python script**: Simple distribution, users run directly
2. **Python package**: Use setuptools for `pip install`
3. **Executable**: PyInstaller for standalone .exe (Windows) or binary (macOS/Linux)

**Recommended**: Start with single script, package later if needed.

### User Installation
```bash
# Clone repository
git clone <repo_url>

# Run script
python iphone-favorites-saver.py /path/to/Photos.sqlite /path/to/photos
```

## Future Technical Enhancements

1. **Python wrapper**: Package with PyExifTool for easier installation
2. **Parallel processing**: Use multiprocessing for faster EXIF writes
3. **Database caching**: Cache database queries for re-runs
4. **GUI**: Add simple Tkinter or PyQt interface
5. **Logging**: Use logging module instead of print statements
6. **Configuration file**: Support .ini or .yaml config for defaults