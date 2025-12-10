#!/usr/bin/env python3
"""Test script to investigate exiftool encoding issues with Hungarian characters."""

import subprocess
import shutil
from pathlib import Path

# Test string with Hungarian characters
TEST_STRING = "Árvíztűrő tükörfúrógép - áéíóöőúüű ÁÉÍÓÖŐÚÜŰ"

# Find a test image
TEST_DIR = Path(__file__).parent / "teszt" / "162APPLE"
test_images = list(TEST_DIR.glob("*.HEIC"))[:1] + list(TEST_DIR.glob("*.JPG"))[:1]

if not test_images:
    print("No test images found!")
    exit(1)

test_image = test_images[0]
print(f"Test image: {test_image}")
print(f"Test string: {TEST_STRING}")
print(f"Test string bytes (UTF-8): {TEST_STRING.encode('utf-8')}")
print()

def run_exiftool(args: list, description: str) -> None:
    """Run exiftool and show results."""
    print(f"\n{'='*60}")
    print(f"TEST: {description}")
    print(f"Command: exiftool {' '.join(args)}")
    print('='*60)

    try:
        result = subprocess.run(
            ["exiftool"] + args,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")
        if result.returncode != 0:
            print(f"Return code: {result.returncode}")
    except Exception as e:
        print(f"ERROR: {e}")

# First, read current state
run_exiftool(
    ["-ImageDescription", "-Description", "-XMP:Description", "-IPTC:Caption-Abstract", str(test_image)],
    "Read current description fields"
)

# Test different encoding approaches
print("\n" + "="*60)
print("ENCODING OPTIONS TO TEST:")
print("="*60)
print("""
1. -charset utf8 (current approach - applies to console I/O)
2. -charset filename=utf8 (for filenames with special chars)
3. -charset iptc=UTF8 (for IPTC fields)
4. -charset exif=UTF8 (for EXIF fields)
5. -codedcharacterset=utf8 (IPTC CodedCharacterSet)
6. Write to XMP instead of EXIF/IPTC (XMP is always UTF-8)
""")

# Show exiftool's charset options
run_exiftool(
    ["-charset", "-h"],
    "Show charset help"
)

# Check what encoding the current description uses
run_exiftool(
    ["-v2", "-ImageDescription", str(test_image)],
    "Verbose read of ImageDescription"
)

# Check IPTC CodedCharacterSet
run_exiftool(
    ["-IPTC:CodedCharacterSet", str(test_image)],
    "Check IPTC CodedCharacterSet"
)

print("\n" + "="*60)
print("RECOMMENDED FIXES TO TRY:")
print("="*60)
print("""
Option A: Use IPTC charset option
  exiftool -charset iptc=UTF8 -codedcharacterset=utf8 -ImageDescription="text" file

Option B: Write to XMP instead (always UTF-8)
  exiftool -XMP:Description="text" file

Option C: Write to both XMP and IPTC with proper encoding
  exiftool -charset iptc=UTF8 -codedcharacterset=utf8 -XMP:Description="text" -IPTC:Caption-Abstract="text" file

Option D: Use -L flag to convert to Latin encoding (if Lightroom expects Latin)
  exiftool -L -ImageDescription="text" file
""")
