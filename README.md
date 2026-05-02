# Lenny's Podcast Recommendations Extractor

Extract and visualize book, movie, and TV show recommendations from Lenny Rachitsky's podcast transcripts.

## Overview

This project extracts recommendations from 295 podcast episodes, downloads cover images, and presents them in beautiful Netflix/Spotify-style interfaces.

**Results:**
- ✅ 467 unique books
- ✅ 102 movies
- ✅ 143 TV shows
- ✅ 98% book cover success rate
- ✅ Complete audit trail of all API attempts

## Quick Start

```bash
# 1. Install dependencies
pip install requests anthropic

# 2. Extract recommendations from podcast transcripts
python3 extract_all_with_api.py

# 3. Download book covers (consolidated v4.0 script)
python3 download_book_covers.py

# 4. Download movie/TV posters
python3 enrich_movies.py

# 5. Generate frontend JSON
python3 convert_csv_to_json.py

# 6. View results
python3 -m http.server 8000
# Open http://localhost:8000/index.html
```

## File Structure

### Main Scripts

| File | Purpose | Version |
|------|---------|---------|
| `extract_all_with_api.py` | Extract recommendations using Claude API | - |
| **`download_book_covers.py`** | **Download book covers (v4.0 consolidated)** | **✅ USE THIS** |
| `enrich_movies.py` | Download movie/TV posters from TMDB | - |
| `convert_csv_to_json.py` | Convert CSV to JSON for frontend | - |
| `analyze_log.py` | Analyze download success rates | - |

### Old Versions (for reference)

| File | Version | Notes |
|------|---------|-------|
| `enrich_images.py` | v1.0 | Basic download, thumbnail only |
| `retry_missing_images.py` | v2.0 | Multiple strategies, still used thumbnail |
| `retry_missing_images_with_logging.py` | v3.0 | Added smallThumbnail, logging |

### Frontend

| File | Description |
|------|-------------|
| `index.html` | Main Netflix-style interface (with toggle) |
| `frontend-netflix.html` | Netflix carousel prototype |
| `frontend-spotify.html` | Spotify grid prototype |
| `frontend-rickrubin.html` | Minimalist scroll prototype |

### Documentation

| File | Description |
|------|-------------|
| `BOOK_IMAGE_DOWNLOAD_LOGIC.md` | Complete logic documentation |
| `IMAGE_RETRIEVAL_SUMMARY.md` | Results and analysis |
| `README.md` | This file |

## Book Cover Download Logic (v4.0)

### Key Improvements

✅ **Prioritizes `smallThumbnail` (zoom=5)** - The key discovery that solved 93% of failures
✅ **Sequential strategy testing** - Stops on first success, saves API calls
✅ **MD5 placeholder detection** - No file size checks (some real covers are small)
✅ **Comprehensive logging** - Every attempt logged to CSV

### Three Search Strategies

```python
# Strategy 1: "exact" (try first)
intitle:"7 Powers" inauthor:"Hamilton Helmer"

# Strategy 2: "title_only" (if exact fails)
intitle:"7 Powers"

# Strategy 3: "loose" (last resort)
7 Powers Hamilton Helmer
```

### Flow

```
For each book:
  Try Strategy 1 → get up to 5 book IDs → try each until real cover found
  If failed, try Strategy 2 → same process
  If failed, try Strategy 3 → same process
  Stop immediately when real cover found
```

See `BOOK_IMAGE_DOWNLOAD_LOGIC.md` for complete details.

## Configuration

### API Keys Required

```python
# Claude API (for extraction)
ANTHROPIC_API_KEY = "sk-ant-api03-..."

# Google Books API (for book covers)
GOOGLE_BOOKS_API_KEY = "AIzaSyCOPa3e..."

# TMDB API (for movie/TV posters)
TMDB_API_KEY = "4b9613e7..."
```

### Rate Limiting

- 1 second between search strategies
- 2 seconds between books
- Handles 503 errors gracefully

## Results

### Book Covers

- **Total books:** 467
- **Successfully downloaded:** ~458 (98%)
- **Remaining failures:** ~9 (not in Google Books database)

### Most Recommended Books

1. High Output Management (7× recommended)
2. Radical Candor (6× recommended)
3. Shoe Dog (6× recommended)
4. The Hard Thing About Hard Things (5× recommended)
5. Man's Search for Meaning (5× recommended)

### Logging

All attempts logged to `book_cover_download_log.csv`:

```csv
timestamp,book_title,book_author,strategy_name,book_id,
image_url,file_size,md5_hash,is_placeholder,final_success
```

Analyze with:
```bash
python3 analyze_log.py
```

## Troubleshooting

### "No real cover found"

Some books aren't in Google Books database. Options:
1. Try Open Library API
2. Manual image upload
3. Use placeholder

### 503 Errors

Google Books rate limiting. The script already has delays, but if you see many 503s:
- Increase `DELAY_BETWEEN_BOOKS` in `download_book_covers.py`
- Run in smaller batches

### Placeholder Images

Known placeholder MD5: `c96309220b9cbd205c36d879d09a3647`

The script automatically detects and retries. If persistent:
- Check `book_cover_download_log.csv` for details
- Manually verify book exists in Google Books

## Version History

- **v1.0** (Apr 2026): Initial extraction, basic image download
- **v2.0** (Apr 2026): Multiple search strategies
- **v3.0** (May 2026): smallThumbnail prioritization, comprehensive logging
- **v4.0** (May 2026): Consolidated script with all improvements ✅

## Technologies

- **Extraction:** Claude API (Sonnet 4.5)
- **Book Covers:** Google Books API
- **Movie/TV Posters:** TMDB API
- **Frontend:** Vanilla HTML/CSS/JavaScript
- **Language:** Python 3.9+

## Credits

Built with [Claude Code](https://claude.com/claude-code) using Claude Sonnet 4.5

Generated on: May 2, 2026

## License

For personal use. API keys and podcast content belong to respective owners.
