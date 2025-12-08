# Photos.sqlite Database Schema Documentation

This document describes the schema of iPhone's Photos.sqlite database, focusing on the tables and relationships needed to extract favorites and descriptions.

## Overview

The Photos.sqlite database is located on iPhone at:
```
/private/var/mobile/Media/PhotoData/Photos.sqlite
```

The schema varies significantly between iOS versions. This document covers iOS 18 and provides notes on older versions.

## Core Tables

### ZASSET

The main table containing photo/video assets.

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZFILENAME | VARCHAR | Original filename (e.g., `IMG_1234.HEIC`) |
| ZDIRECTORY | VARCHAR | Directory path (e.g., `DCIM/162APPLE`) |
| ZFAVORITE | INTEGER | 1 = favorited, 0 = not favorited |
| ZTRASHEDSTATE | INTEGER | 0 = not trashed, non-zero = in trash |
| ZADDITIONALATTRIBUTES | INTEGER | FK to ZADDITIONALASSETATTRIBUTES.Z_PK (iOS 18+) |

**iOS Version Differences:**
- iOS 18+: Uses `ZADDITIONALATTRIBUTES` column
- Older iOS: Used `ZADDITIONALASSETATTRIBUTES` column, or join via `ZASSET.Z_PK = ZADDITIONALASSETATTRIBUTES.ZASSET`

### ZADDITIONALASSETATTRIBUTES

Extended attributes for assets including titles and links to descriptions.

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZASSET | INTEGER | FK back to ZASSET.Z_PK |
| ZASSETDESCRIPTION | INTEGER | FK to ZASSETDESCRIPTION.Z_PK (iOS 18+) |
| ZTITLE | VARCHAR | User-assigned title |
| ZORIGINALFILENAME | VARCHAR | Original filename before any edits |
| ZTIMEZONENAME | VARCHAR | Timezone info |

### ZASSETDESCRIPTION

Contains user-entered descriptions (captions) for photos.

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZASSETATTRIBUTES | INTEGER | FK to ZADDITIONALASSETATTRIBUTES.Z_PK |
| ZLONGDESCRIPTION | VARCHAR | User-entered description/caption |

**Note:** Both `ZASSETATTRIBUTES` (in ZASSETDESCRIPTION) and `ZASSETDESCRIPTION` (in ZADDITIONALASSETATTRIBUTES) exist, providing bidirectional linking.

### ZEXTENDEDATTRIBUTES

EXIF and technical metadata.

| Column | Type | Description |
|--------|------|-------------|
| Z_PK | INTEGER | Primary key |
| ZASSET | INTEGER | FK to ZASSET.Z_PK |
| ZCAMERAMAKE | VARCHAR | Camera manufacturer |
| ZCAMERAMODEL | VARCHAR | Camera model |
| ZLENSMODEL | VARCHAR | Lens info |
| ZLATITUDE | FLOAT | GPS latitude |
| ZLONGITUDE | FLOAT | GPS longitude |
| ZDATECREATED | TIMESTAMP | Original creation date |

## Table Relationships

### iOS 18+ Schema

```
ZASSET
    │
    ├── ZADDITIONALATTRIBUTES ──→ ZADDITIONALASSETATTRIBUTES.Z_PK
    │                                      │
    │                                      ├── ZASSETDESCRIPTION ──→ ZASSETDESCRIPTION.Z_PK
    │                                      │                                │
    │                                      │                                └── ZLONGDESCRIPTION
    │                                      │
    │                                      └── ZTITLE
    │
    └── Z_PK ──→ ZEXTENDEDATTRIBUTES.ZASSET
```

### Older iOS Schema (pre-iOS 18)

```
ZASSET
    │
    ├── Z_PK ──→ ZADDITIONALASSETATTRIBUTES.ZASSET
    │                      │
    │                      └── Z_PK ←── ZASSETDESCRIPTION.ZASSETATTRIBUTES
    │                                              │
    │                                              └── ZLONGDESCRIPTION
    │
    └── Z_PK ──→ ZEXTENDEDATTRIBUTES.ZASSET
```

## SQL Queries

### iOS 18: Get Favorites and Descriptions

```sql
SELECT
    ZASSET.ZFILENAME,
    ZASSET.ZDIRECTORY,
    ZASSET.ZFAVORITE,
    COALESCE(
        NULLIF(ZASSETDESCRIPTION.ZLONGDESCRIPTION, ''),
        NULLIF(ZADDITIONALASSETATTRIBUTES.ZTITLE, ''),
        ''
    ) AS DESCRIPTION
FROM ZASSET
LEFT JOIN ZADDITIONALASSETATTRIBUTES
    ON ZASSET.ZADDITIONALATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK
LEFT JOIN ZASSETDESCRIPTION
    ON ZADDITIONALASSETATTRIBUTES.ZASSETDESCRIPTION = ZASSETDESCRIPTION.Z_PK
WHERE ZASSET.ZTRASHEDSTATE = 0
  AND (ZASSET.ZFAVORITE = 1
       OR (ZASSETDESCRIPTION.ZLONGDESCRIPTION IS NOT NULL
           AND ZASSETDESCRIPTION.ZLONGDESCRIPTION != ''))
```

### Older iOS: Get Favorites and Descriptions

```sql
SELECT
    ZASSET.ZFILENAME,
    ZASSET.ZDIRECTORY,
    ZASSET.ZFAVORITE,
    COALESCE(
        NULLIF(ZASSETDESCRIPTION.ZLONGDESCRIPTION, ''),
        NULLIF(ZADDITIONALASSETATTRIBUTES.ZTITLE, ''),
        ''
    ) AS DESCRIPTION
FROM ZASSET
LEFT JOIN ZADDITIONALASSETATTRIBUTES
    ON ZASSET.Z_PK = ZADDITIONALASSETATTRIBUTES.ZASSET
LEFT JOIN ZASSETDESCRIPTION
    ON ZASSETDESCRIPTION.ZASSETATTRIBUTES = ZADDITIONALASSETATTRIBUTES.Z_PK
WHERE ZASSET.ZTRASHEDSTATE = 0
  AND (ZASSET.ZFAVORITE = 1
       OR (ZASSETDESCRIPTION.ZLONGDESCRIPTION IS NOT NULL
           AND ZASSETDESCRIPTION.ZLONGDESCRIPTION != ''))
```

### Detecting iOS Version

Check for the presence of `ZADDITIONALATTRIBUTES` column in ZASSET:

```sql
PRAGMA table_info(ZASSET)
```

If `ZADDITIONALATTRIBUTES` exists → iOS 18+
If only `Z_PK` for joining → Older iOS

## Statistics (Sample Database)

From an iOS 18 Photos.sqlite with ~18,000 photos:

| Metric | Count |
|--------|-------|
| Total non-trashed assets | 17,879 |
| Favorites | 839 |
| Assets with descriptions | 287 |

## Field Priority for Descriptions

When extracting descriptions, use this priority order:
1. `ZASSETDESCRIPTION.ZLONGDESCRIPTION` - User-entered caption (iOS 18)
2. `ZADDITIONALASSETATTRIBUTES.ZTITLE` - User-assigned title
3. `ZEXTENDEDATTRIBUTES.ZCAPTION` - (older iOS versions)

## Common Issues

### Character Encoding
- The database uses UTF-8 encoding
- Hungarian/special characters display correctly when read with proper encoding
- Console output may show garbled text if terminal doesn't support UTF-8

### Missing Files
- Database may reference files that no longer exist on disk
- Always verify file existence before processing
- Trashed files (`ZTRASHEDSTATE != 0`) should typically be excluded

### Schema Changes
- Apple changes the schema between iOS versions without documentation
- Always query `sqlite_master` and `PRAGMA table_info()` to detect schema
- Build queries dynamically based on available columns

## Useful Discovery Queries

### List All Tables
```sql
SELECT name FROM sqlite_master WHERE type='table' ORDER BY name
```

### Find Columns Containing a Pattern
```sql
-- For each table, check columns
PRAGMA table_info(table_name)
```

### Count Favorites by Directory
```sql
SELECT ZDIRECTORY, COUNT(*) as cnt
FROM ZASSET
WHERE ZFAVORITE = 1 AND ZTRASHEDSTATE = 0
GROUP BY ZDIRECTORY
ORDER BY cnt DESC
```

### Find Assets with Descriptions
```sql
SELECT COUNT(*)
FROM ZASSETDESCRIPTION
WHERE ZLONGDESCRIPTION IS NOT NULL AND ZLONGDESCRIPTION != ''
```
