# Book Image Retrieval - Database & Logging System

## Overview
This system tracks all attempts to download book cover images from Google Books API, providing comprehensive logging for debugging and analysis.

## Database File
**Location:** `/Users/vivekgupta/Downloads/lennyrecs/book_image_retrieval_log.csv`

## Database Schema

| Field | Description |
|-------|-------------|
| `timestamp` | ISO 8601 timestamp of the attempt |
| `book_title` | Full title of the book |
| `book_author` | Author name (or "N/A") |
| `strategy_name` | Search strategy used: `exact`, `title_only`, `loose`, or `all_strategies` |
| `strategy_number` | Numeric strategy ID (1, 2, 3, or 0 for summary rows) |
| `book_id` | Google Books unique book identifier |
| `api_url` | Full Google Books API URL called |
| `image_url` | Direct image URL returned by API |
| `download_attempted` | Boolean - whether download was attempted |
| `download_success` | Boolean - whether download succeeded |
| `file_path` | Local filesystem path where image was saved |
| `file_size_bytes` | Size of downloaded file in bytes |
| `md5_hash` | MD5 checksum of downloaded file |
| `is_placeholder` | Boolean - true if image is placeholder "image not available" |
| `error_message` | Description of any errors encountered |
| `match_score` | Similarity score (0-1) between search and result |
| `final_success` | Boolean - true only if real cover was found and saved |

## Search Strategies

### Strategy 1: Exact (`exact`)
- **Query format:** `intitle:"Book Title" inauthor:"Author Name"`
- **Best for:** Books with well-known authors and exact title matches
- **Success rate:** 34% (9/26 attempts)
- **Example:** `intitle:"The Myth of Sisyphus" inauthor:"Albert Camus"`

### Strategy 2: Title Only (`title_only`)
- **Query format:** `intitle:"Book Title"`
- **Best for:** Books where author is N/A or generic titles
- **Success rate:** 31% (7/22 attempts)
- **Example:** `intitle:"Good to Great"`

### Strategy 3: Loose (`loose`)
- **Query format:** `Book Title Author Name` (no quotes, no operators)
- **Best for:** Books with unconventional titles or name variations
- **Success rate:** 20% (4/20 attempts)
- **Example:** `From Third World to First Lee Kuan Yew`

## Results Summary

### Overall Performance
- **Books attempted:** 44
- **Books succeeded:** 20
- **Books still missing:** 24
- **Success rate:** 45%

### Successful Downloads

| # | Book Title | Strategy | Size | Book ID |
|---|-----------|----------|------|---------|
| 1 | Accelerate | title_only | 20,989 bytes | Kax-DwAAQBAJ |
| 2 | Carry On, Jeeves | exact | 34,519 bytes | OL5TEAAAQBAJ |
| 3 | Competing Against Luck | exact | 20,556 bytes | zGd_CwAAQBAJ |
| 4 | Dare to Lead Like a Girl | loose | 18,898 bytes | oyCAEQAAQBAJ |
| 5 | From Third World to First | loose | 20,855 bytes | 1c71I4dPZdkC |
| 6 | Good to Great | title_only | 30,975 bytes | pJNt2ZFFT3sC |
| 7 | How Brands Grow | exact | 66,199 bytes | tSdHDwAAQBAJ |
| 8 | How to Get Rich | title_only | 148,950 bytes | ensxD4a3FAsC |
| 9 | Mistakes Were Made (But Not by Me) | exact | 11,776 bytes | vZkGNIpAsTEC |
| 10 | Out of Sheer Rage | exact | 26,449 bytes | uqs2RBrY-uAC |
| 11 | Pachinko | exact | 15,860 bytes | odirEAAAQBAJ |
| 12 | Roald Dahl books (including Witches and Matilda) | loose | 10,496 bytes | nwl1EQAAQBAJ |
| 13 | The Boy, the Mole, the Fox, and the Horse | title_only | 14,811 bytes | ID9fEAAAQBAJ |
| 14 | The Fabric of Reality | loose | 22,252 bytes | ex5xge75SR4C |
| 15 | The Myth of Sisyphus | exact | 37,361 bytes | zG9wDwAAQBAJ |
| 16 | The Person and the Situation | title_only | 31,237 bytes | PHbrAwAAQBAJ |
| 17 | The Road to Reality | exact | 123,239 bytes | SkwiEAAAQBAJ |
| 18 | The Wandering Earth | title_only | 24,916 bytes | 854OEAAAQBAJ |
| 19 | The Writer's Journey | title_only | 55,254 bytes | XU-IEAAAQBAJ |
| 20 | Treasure Island | exact | 26,051 bytes | y-gsEAAAQBAJ |

### Still Missing (24 books)

1. 15 Commitments of Conscious Leadership
2. **7 Powers** ← High priority (all book IDs return placeholders)
3. A Deepness in the Sky
4. Breakneck
5. End of Average
6. Founding Sales
7. Getting Real
8. It's Not How Good You Are, It's How Good You Want to Be
9. Kindred
10. Le Ton beau de Marot
11. Metabolical
12. Obviously Awesome
13. Orbiting the Giant Hairball: A Corporate Fool's Guide to Surviving with Grace
14. Power: Why Some People Have It and Others Don't
15. Radical Focus
16. **Range** ← High priority
17. Replacing Guilt
18. Revolt of the Public
19. Simple Path to Wealth
20. Snuggle Puppy
21. Strong Product People
22. The Case Against Reality
23. The Elements of Thinking in Systems
24. Tress by the Emerald Sea

## Key Findings

### Placeholder Detection
- **Placeholder MD5:** `c96309220b9cbd205c36d879d09a3647`
- **Typical size:** 15,567 bytes
- **Issue:** Google Books API returns valid `imageLinks` but actual image is "Image not available" placeholder
- **Solution:** Script tries multiple book IDs per book until finding real cover

### Book ID Multiplicity
Some books have multiple Google Books IDs - some with real covers, some with placeholders:

**Example: "7 Powers"**
- Book ID `heEuvgAACAAJ` → Placeholder (15,567 bytes)
- Book ID `9p1evgAACAAJ` → Placeholder (15,567 bytes)
- All discovered IDs return placeholders - likely no cover available in Google Books

**Example: "Accelerate"** (SUCCESS)
- Multiple IDs tried, one with real cover found
- Final: Book ID `Kax-DwAAQBAJ` → Real cover (20,989 bytes)

### API Rate Limiting
- **Issue:** 503 Service Unavailable errors from Google Books API
- **Solution:** 1 second delay between strategies, 2 seconds between books
- **Impact:** Script takes ~5-10 minutes to process 44 books

## Files in This System

| File | Purpose |
|------|---------|
| `retry_missing_images_with_logging.py` | Main script with comprehensive CSV logging |
| `book_image_retrieval_log.csv` | Database of all attempts (92 rows for 44 books) |
| `analyze_log.py` | Analysis script for statistics and summaries |
| `IMAGE_RETRIEVAL_SUMMARY.md` | This documentation file |

## Usage

### Running the retry script:
```bash
source venv/bin/activate
python3 retry_missing_images_with_logging.py
```

### Analyzing the log:
```bash
python3 analyze_log.py
```

### Querying the CSV database:
```bash
# Count successes
grep "True" book_image_retrieval_log.csv | grep "final_success" | wc -l

# Find all attempts for a specific book
grep "7 Powers" book_image_retrieval_log.csv

# See which strategy worked best
cut -d',' -f4,17 book_image_retrieval_log.csv | grep "True" | sort | uniq -c
```

## Next Steps

### For the 24 missing books:
1. **Manual search** - Some books may not be in Google Books (e.g., "Getting Real" by 37signals)
2. **Alternative sources** - Try Open Library API, Amazon Product Advertising API
3. **Custom uploads** - For books unavailable in any API, source images manually
4. **Title variations** - Some books may have slightly different titles in Google Books

### Recommended priorities:
- **7 Powers** - Highly recommended book, all API attempts failed
- **Range** - Popular book, likely available with different search terms
- **Obviously Awesome** - Recent book, might be in Google Books under different edition
