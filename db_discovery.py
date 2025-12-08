#!/usr/bin/env python3
"""Database discovery script for iOS 18 Photos.sqlite schema."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "teszt" / "Photos-20251206_2140.sqlite"


def print_separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f" {title}")
    print('=' * 60)


def get_all_tables(cursor: sqlite3.Cursor) -> list[str]:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def get_table_columns(cursor: sqlite3.Cursor, table: str) -> list[tuple[str, str]]:
    cursor.execute(f"PRAGMA table_info({table})")
    return [(row[1], row[2]) for row in cursor.fetchall()]


def search_column_in_tables(cursor: sqlite3.Cursor, column_pattern: str) -> None:
    """Search for columns matching a pattern across all tables."""
    print_separator(f"Tables containing '{column_pattern}' columns")
    tables = get_all_tables(cursor)
    for table in tables:
        columns = get_table_columns(cursor, table)
        matching = [c for c in columns if column_pattern.upper() in c[0].upper()]
        if matching:
            print(f"\n{table}:")
            for col_name, col_type in matching:
                print(f"  - {col_name} ({col_type})")


def explore_zasset(cursor: sqlite3.Cursor) -> None:
    """Explore ZASSET table structure."""
    print_separator("ZASSET Table Structure")
    columns = get_table_columns(cursor, "ZASSET")
    print(f"Total columns: {len(columns)}\n")

    # Show columns related to favorites, descriptions, filenames
    interesting_patterns = ['FAVORITE', 'DESCRIPTION', 'FILENAME', 'DIRECTORY', 'TITLE', 'CAPTION', 'Z_PK', 'ZADDITIONAL']
    for pattern in interesting_patterns:
        matching = [c for c in columns if pattern.upper() in c[0].upper()]
        if matching:
            print(f"Columns matching '{pattern}':")
            for col_name, col_type in matching:
                print(f"  - {col_name} ({col_type})")


def explore_description_tables(cursor: sqlite3.Cursor) -> None:
    """Look for tables that might contain descriptions."""
    print_separator("Tables potentially containing descriptions")

    tables = get_all_tables(cursor)
    desc_tables = [t for t in tables if 'DESCRIPTION' in t.upper() or 'EXTENDED' in t.upper() or 'ADDITIONAL' in t.upper()]

    for table in desc_tables:
        print(f"\n{table}:")
        columns = get_table_columns(cursor, table)
        for col_name, col_type in columns:
            print(f"  - {col_name} ({col_type})")


def sample_favorites(cursor: sqlite3.Cursor) -> None:
    """Find some favorite photos to understand the data."""
    print_separator("Sample FAVORITE entries from ZASSET")

    cursor.execute("""
        SELECT Z_PK, ZFILENAME, ZDIRECTORY, ZFAVORITE, ZTRASHEDSTATE
        FROM ZASSET
        WHERE ZFAVORITE = 1
        LIMIT 10
    """)
    rows = cursor.fetchall()
    print(f"Found {len(rows)} favorite(s) (showing up to 10):\n")
    for row in rows:
        print(f"  Z_PK={row[0]}, FILE={row[1]}, DIR={row[2]}, FAV={row[3]}, TRASH={row[4]}")


def explore_zassetdescription(cursor: sqlite3.Cursor) -> None:
    """Explore ZASSETDESCRIPTION table if it exists."""
    print_separator("ZASSETDESCRIPTION Table Exploration")

    tables = get_all_tables(cursor)
    if 'ZASSETDESCRIPTION' not in tables:
        print("ZASSETDESCRIPTION table does NOT exist!")
        return

    columns = get_table_columns(cursor, 'ZASSETDESCRIPTION')
    print("Columns:")
    for col_name, col_type in columns:
        print(f"  - {col_name} ({col_type})")

    # Check for non-empty descriptions
    cursor.execute("SELECT COUNT(*) FROM ZASSETDESCRIPTION WHERE ZLONGDESCRIPTION IS NOT NULL AND ZLONGDESCRIPTION != ''")
    count = cursor.fetchone()[0]
    print(f"\nRows with non-empty ZLONGDESCRIPTION: {count}")

    if count > 0:
        cursor.execute("""
            SELECT Z_PK, ZASSETATTRIBUTES, ZLONGDESCRIPTION
            FROM ZASSETDESCRIPTION
            WHERE ZLONGDESCRIPTION IS NOT NULL AND ZLONGDESCRIPTION != ''
            LIMIT 5
        """)
        print("\nSample descriptions:")
        for row in cursor.fetchall():
            desc = row[2][:50] + "..." if len(row[2]) > 50 else row[2]
            print(f"  Z_PK={row[0]}, ZASSETATTRIBUTES={row[1]}, DESC='{desc}'")


def explore_zadditionalassetattributes(cursor: sqlite3.Cursor) -> None:
    """Explore ZADDITIONALASSETATTRIBUTES table."""
    print_separator("ZADDITIONALASSETATTRIBUTES Table Exploration")

    tables = get_all_tables(cursor)
    if 'ZADDITIONALASSETATTRIBUTES' not in tables:
        print("ZADDITIONALASSETATTRIBUTES table does NOT exist!")
        return

    columns = get_table_columns(cursor, 'ZADDITIONALASSETATTRIBUTES')
    print(f"Total columns: {len(columns)}")

    # Show relevant columns
    relevant = [c for c in columns if any(p in c[0].upper() for p in ['Z_PK', 'ZASSET', 'TITLE', 'DESCRIPTION', 'CAPTION'])]
    print("\nRelevant columns:")
    for col_name, col_type in relevant:
        print(f"  - {col_name} ({col_type})")


def find_join_path(cursor: sqlite3.Cursor) -> None:
    """Figure out how to join ZASSET to ZASSETDESCRIPTION."""
    print_separator("Finding JOIN path: ZASSET -> ZASSETDESCRIPTION")

    tables = get_all_tables(cursor)

    # Check if ZASSETDESCRIPTION.ZASSETATTRIBUTES links to ZADDITIONALASSETATTRIBUTES.Z_PK
    if 'ZASSETDESCRIPTION' in tables and 'ZADDITIONALASSETATTRIBUTES' in tables:
        # Get a sample to understand the relationship
        cursor.execute("""
            SELECT
                ad.Z_PK as AAA_PK,
                ad.ZASSET as AAA_ZASSET,
                d.Z_PK as DESC_PK,
                d.ZASSETATTRIBUTES as DESC_ZASSETATTRIBUTES,
                d.ZLONGDESCRIPTION
            FROM ZADDITIONALASSETATTRIBUTES ad
            LEFT JOIN ZASSETDESCRIPTION d ON d.ZASSETATTRIBUTES = ad.Z_PK
            WHERE d.ZLONGDESCRIPTION IS NOT NULL AND d.ZLONGDESCRIPTION != ''
            LIMIT 5
        """)
        rows = cursor.fetchall()
        if rows:
            print("Join via ZASSETDESCRIPTION.ZASSETATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK works!")
            print("\nSample joined data:")
            for row in rows:
                desc = row[4][:40] + "..." if row[4] and len(row[4]) > 40 else row[4]
                print(f"  AAA.Z_PK={row[0]}, AAA.ZASSET={row[1]}, DESC.Z_PK={row[2]}, DESC='{desc}'")


def test_full_query(cursor: sqlite3.Cursor) -> None:
    """Test the full query to get favorites and descriptions."""
    print_separator("Testing FULL QUERY: ZASSET + ZADDITIONALASSETATTRIBUTES + ZASSETDESCRIPTION")

    # iOS 18: ZASSET.ZADDITIONALATTRIBUTES -> ZADDITIONALASSETATTRIBUTES.Z_PK
    # ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION -> ZASSETDESCRIPTION.Z_PK
    query = """
        SELECT
            ZASSET.Z_PK,
            ZASSET.ZFILENAME,
            ZASSET.ZDIRECTORY,
            ZASSET.ZFAVORITE,
            ZASSET.ZTRASHEDSTATE,
            ZADDITIONALASSETATTRIBUTES.Z_PK as AAA_PK,
            ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION as AAA_DESC_FK,
            ZASSETDESCRIPTION.ZLONGDESCRIPTION
        FROM ZASSET
        LEFT JOIN ZADDITIONALASSETATTRIBUTES ON ZASSET.ZADDITIONALATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK
        LEFT JOIN ZASSETDESCRIPTION ON ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION = ZASSETDESCRIPTION.Z_PK
        WHERE ZASSET.ZTRASHEDSTATE = 0
          AND (ZASSET.ZFAVORITE = 1 OR (ZASSETDESCRIPTION.ZLONGDESCRIPTION IS NOT NULL AND ZASSETDESCRIPTION.ZLONGDESCRIPTION != ''))
        LIMIT 20
    """

    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        print(f"Query returned {len(rows)} row(s)\n")

        for row in rows:
            desc = row[7][:30] + "..." if row[7] and len(row[7]) > 30 else (row[7] or '<none>')
            print(f"  Z_PK={row[0]}, FILE={row[1]}, FAV={row[3]}, DESC='{desc}'")

    except sqlite3.Error as e:
        print(f"Query FAILED: {e}")

        # Try alternative: ZASSETDESCRIPTION.ZASSETATTRIBUTES -> ZADDITIONALASSETATTRIBUTES.Z_PK
        print("\nTrying alternative join via ZASSETDESCRIPTION.ZASSETATTRIBUTES...")
        alt_query = """
            SELECT
                ZASSET.Z_PK,
                ZASSET.ZFILENAME,
                ZASSET.ZDIRECTORY,
                ZASSET.ZFAVORITE,
                ZASSET.ZTRASHEDSTATE,
                ZADDITIONALASSETATTRIBUTES.Z_PK as AAA_PK,
                ZASSETDESCRIPTION.ZLONGDESCRIPTION
            FROM ZASSET
            LEFT JOIN ZADDITIONALASSETATTRIBUTES ON ZASSET.ZADDITIONALATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK
            LEFT JOIN ZASSETDESCRIPTION ON ZASSETDESCRIPTION.ZASSETATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK
            WHERE ZASSET.ZTRASHEDSTATE = 0
              AND (ZASSET.ZFAVORITE = 1 OR (ZASSETDESCRIPTION.ZLONGDESCRIPTION IS NOT NULL AND ZASSETDESCRIPTION.ZLONGDESCRIPTION != ''))
            LIMIT 20
        """
        cursor.execute(alt_query)
        rows = cursor.fetchall()
        print(f"Alternative query returned {len(rows)} row(s)\n")

        for row in rows:
            desc = row[6][:30] + "..." if row[6] and len(row[6]) > 30 else (row[6] or '<none>')
            print(f"  Z_PK={row[0]}, FILE={row[1]}, FAV={row[3]}, DESC='{desc}'")


def count_totals(cursor: sqlite3.Cursor) -> None:
    """Count totals for verification."""
    print_separator("Database Statistics")

    cursor.execute("SELECT COUNT(*) FROM ZASSET WHERE ZTRASHEDSTATE = 0")
    total = cursor.fetchone()[0]
    print(f"Total non-trashed assets: {total}")

    cursor.execute("SELECT COUNT(*) FROM ZASSET WHERE ZFAVORITE = 1 AND ZTRASHEDSTATE = 0")
    favorites = cursor.fetchone()[0]
    print(f"Favorites (non-trashed): {favorites}")

    cursor.execute("SELECT COUNT(*) FROM ZASSETDESCRIPTION WHERE ZLONGDESCRIPTION IS NOT NULL AND ZLONGDESCRIPTION != ''")
    descriptions = cursor.fetchone()[0]
    print(f"Assets with descriptions: {descriptions}")


def check_zasset_join_column(cursor: sqlite3.Cursor) -> None:
    """Check what column in ZASSET links to ZADDITIONALASSETATTRIBUTES."""
    print_separator("Checking ZASSET -> ZADDITIONALASSETATTRIBUTES relationship")

    columns = get_table_columns(cursor, 'ZASSET')
    matching = [c for c in columns if 'ADDITIONAL' in c[0].upper()]
    print("ZASSET columns mentioning 'ADDITIONAL':")
    for col_name, col_type in matching:
        print(f"  - {col_name} ({col_type})")

    # Check sample values - iOS 18 uses ZADDITIONALATTRIBUTES (not ZADDITIONALASSETATTRIBUTES)
    cursor.execute("""
        SELECT Z_PK, ZADDITIONALATTRIBUTES
        FROM ZASSET
        WHERE ZADDITIONALATTRIBUTES IS NOT NULL
        LIMIT 5
    """)
    rows = cursor.fetchall()
    if rows:
        print("\nSample ZASSET.ZADDITIONALATTRIBUTES values:")
        for row in rows:
            print(f"  ZASSET.Z_PK={row[0]} -> ZADDITIONALATTRIBUTES={row[1]}")

    # Compare with ZADDITIONALASSETATTRIBUTES.Z_PK
    cursor.execute("""
        SELECT a.Z_PK, a.ZADDITIONALATTRIBUTES, aa.Z_PK as AA_PK, aa.ZASSET
        FROM ZASSET a
        LEFT JOIN ZADDITIONALASSETATTRIBUTES aa ON a.ZADDITIONALATTRIBUTES = aa.Z_PK
        WHERE a.ZADDITIONALATTRIBUTES IS NOT NULL
        LIMIT 5
    """)
    rows = cursor.fetchall()
    print("\nVerifying join ZASSET.ZADDITIONALATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK:")
    for row in rows:
        match = "MATCH" if row[1] == row[2] else "MISMATCH"
        print(f"  ZASSET.Z_PK={row[0]}, ZASSET.ZADDITIONALATTRIBUTES={row[1]}, AA.Z_PK={row[2]}, AA.ZASSET={row[3]} [{match}]")


def main():
    print(f"Database: {DB_PATH}")
    print(f"Exists: {DB_PATH.exists()}")

    if not DB_PATH.exists():
        print("ERROR: Database file not found!")
        return

    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        # Run all discovery functions
        search_column_in_tables(cursor, 'FAVORITE')
        search_column_in_tables(cursor, 'DESCRIPTION')
        search_column_in_tables(cursor, 'LONGDESCRIPTION')

        explore_zasset(cursor)
        explore_description_tables(cursor)
        explore_zassetdescription(cursor)
        explore_zadditionalassetattributes(cursor)

        check_zasset_join_column(cursor)
        find_join_path(cursor)

        sample_favorites(cursor)
        count_totals(cursor)

        test_full_query(cursor)


if __name__ == "__main__":
    main()
