#!/usr/bin/env python3
"""Quick check to see if there are any favorites in the 162APPLE folder."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "teszt" / "Photos-20251206_2140.sqlite"

with sqlite3.connect(DB_PATH) as conn:
    cursor = conn.cursor()

    # Count favorites in 162APPLE
    cursor.execute("""
        SELECT COUNT(*) FROM ZASSET
        WHERE ZFAVORITE = 1 AND ZTRASHEDSTATE = 0 AND ZDIRECTORY LIKE '%162APPLE%'
    """)
    count = cursor.fetchone()[0]
    print(f"Favorites in 162APPLE: {count}")

    # Show some favorites from 162APPLE if any
    cursor.execute("""
        SELECT ZFILENAME, ZDIRECTORY, ZFAVORITE FROM ZASSET
        WHERE ZFAVORITE = 1 AND ZTRASHEDSTATE = 0 AND ZDIRECTORY LIKE '%162APPLE%'
        LIMIT 10
    """)
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row[0]} in {row[1]}")

    # What directories have favorites?
    print("\nDirectories with favorites:")
    cursor.execute("""
        SELECT ZDIRECTORY, COUNT(*) as cnt FROM ZASSET
        WHERE ZFAVORITE = 1 AND ZTRASHEDSTATE = 0
        GROUP BY ZDIRECTORY
        ORDER BY cnt DESC
        LIMIT 20
    """)
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
