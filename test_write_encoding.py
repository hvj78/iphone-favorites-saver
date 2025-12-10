#!/usr/bin/env python3
"""Test different approaches to write UTF-8 descriptions with exiftool."""

import subprocess
import shutil
from pathlib import Path
import tempfile
import os

# Test string with Hungarian characters
TEST_STRING = "Teszt: áéíóöőúüű ÁÉÍÓÖŐÚÜŰ és … ellipszis"

# Find a test image and make a copy
TEST_DIR = Path(__file__).parent / "teszt" / "162APPLE"
source_image = list(TEST_DIR.glob("*.JPG"))[0]  # Use JPG for easier testing

print(f"Source image: {source_image}")
print(f"Test string: {TEST_STRING}")
print(f"Test string UTF-8 hex: {TEST_STRING.encode('utf-8').hex()}")
print()

# Create temp copies for each test
temp_dir = Path(tempfile.mkdtemp())
print(f"Temp dir: {temp_dir}")


def make_test_copy(name: str) -> Path:
    dest = temp_dir / f"{name}.jpg"
    shutil.copy(source_image, dest)
    return dest


def run_exiftool_and_check(args: list, test_file: Path, description: str) -> None:
    """Run exiftool write, then read back and check."""
    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"Command: exiftool {' '.join(str(a) for a in args)}")
    print('='*70)

    # Write
    result = subprocess.run(
        ["exiftool", "-overwrite_original"] + args + [str(test_file)],
        capture_output=True,
    )
    if result.returncode != 0:
        print(f"WRITE FAILED: {result.stderr}")
        return

    # Check raw bytes of ImageDescription
    result = subprocess.run(
        ["exiftool", "-b", "-ImageDescription", str(test_file)],
        capture_output=True
    )
    raw_bytes = result.stdout
    print(f"ImageDescription raw bytes (hex): {raw_bytes.hex()}")

    # Check if it matches expected UTF-8
    expected_utf8 = TEST_STRING.encode('utf-8')
    if raw_bytes == expected_utf8:
        print("SUCCESS: BYTES MATCH EXPECTED UTF-8!")
    else:
        print(f"FAIL: BYTES DON'T MATCH")
        print(f"  Expected: {expected_utf8.hex()}")
        print(f"  Got:      {raw_bytes.hex()}")

    # Also check XMP
    result = subprocess.run(
        ["exiftool", "-b", "-XMP:Description", str(test_file)],
        capture_output=True
    )
    if result.stdout:
        print(f"XMP:Description raw bytes (hex): {result.stdout.hex()}")
        if result.stdout == expected_utf8:
            print("SUCCESS: XMP BYTES MATCH EXPECTED UTF-8!")


# Test 1: Current approach (what we have now) - likely fails on Windows
test1 = make_test_copy("test1_current")
run_exiftool_and_check(
    ["-charset", "utf8", f"-ImageDescription={TEST_STRING}", f"-Description={TEST_STRING}"],
    test1,
    "Current approach: -charset utf8 (command line)"
)

# Test 2: Using argfile with UTF-8 BOM
test2 = make_test_copy("test2_argfile_bom")
argfile = temp_dir / "args_bom.txt"
with open(argfile, 'w', encoding='utf-8-sig') as f:  # UTF-8 with BOM
    f.write(f"-ImageDescription={TEST_STRING}\n")
    f.write(f"-Description={TEST_STRING}\n")
run_exiftool_and_check(
    ["-@", str(argfile)],
    test2,
    "Using argfile (-@) with UTF-8 BOM"
)

# Test 3: Using argfile without BOM but with -charset
test3 = make_test_copy("test3_argfile_charset")
argfile3 = temp_dir / "args_charset.txt"
with open(argfile3, 'w', encoding='utf-8') as f:
    f.write(f"-charset\n")
    f.write(f"filename=utf8\n")
    f.write(f"-ImageDescription={TEST_STRING}\n")
    f.write(f"-Description={TEST_STRING}\n")
run_exiftool_and_check(
    ["-@", str(argfile3)],
    test3,
    "Using argfile with -charset in file"
)

# Test 4: Write to XMP only
test4 = make_test_copy("test4_xmp_only")
argfile4 = temp_dir / "args_xmp.txt"
with open(argfile4, 'w', encoding='utf-8-sig') as f:
    f.write(f"-XMP:Description={TEST_STRING}\n")
run_exiftool_and_check(
    ["-@", str(argfile4)],
    test4,
    "XMP only via argfile"
)

# Test 5: Combined approach - write to both EXIF and XMP via argfile
test5 = make_test_copy("test5_combined")
argfile5 = temp_dir / "args_combined.txt"
with open(argfile5, 'w', encoding='utf-8-sig') as f:
    f.write(f"-ImageDescription={TEST_STRING}\n")
    f.write(f"-XMP:Description={TEST_STRING}\n")
run_exiftool_and_check(
    ["-@", str(argfile5)],
    test5,
    "Combined EXIF + XMP via argfile with BOM"
)

print(f"\n{'='*70}")
print(f"Test files saved to: {temp_dir}")
print("Open these files in Lightroom to verify which encoding works!")
print('='*70)
