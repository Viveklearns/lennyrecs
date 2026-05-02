# Book Cover Image Download Logic

## Overview
This document describes the complete logic for downloading book cover images from Google Books API with comprehensive placeholder detection and logging.

## Image Quality Hierarchy (Priority Order)

Google Books API provides multiple image URLs per book. We prioritize them as follows:

```
Priority 1: "large"         → Best quality (rare, usually not available)
Priority 2: "medium"        → Good quality (rare, usually not available)
Priority 3: "smallThumbnail" → zoom=5 parameter (BEST WORKING OPTION ✅)
Priority 4: "thumbnail"      → zoom=1 parameter (often becomes placeholder)
```

**Key Discovery:** The `smallThumbnail` field with `zoom=5` consistently provides real book covers, while `thumbnail` with `zoom=1` (or modified to `zoom=2`) often returns placeholder images.

## Search Strategy Progression (Sequential)

We use 3 search strategies, tried **sequentially** (not in parallel) to minimize API calls:

### Strategy 1: "exact" (Most Precise)
```
Query: intitle:"Book Title" inauthor:"Author Name"
Example: intitle:"7 Powers" inauthor:"Hamilton Helmer"
```
- Best for books with known authors
- Highest precision, lowest recall
- Try this first for 90% of books

### Strategy 2: "title_only" (Medium Precision)
```
Query: intitle:"Book Title"
Example: intitle:"7 Powers"
```
- For books where author is unknown (N/A)
- For books with common author names causing conflicts
- Medium precision, medium recall

### Strategy 3: "loose" (Broadest Search)
```
Query: Book Title Author Name (no operators)
Example: 7 Powers Hamilton Helmer
```
- Fallback for difficult books
- Catches books with title variations
- Lowest precision, highest recall

**Important:** We stop as soon as any strategy succeeds. Don't waste API calls on subsequent strategies.

## Placeholder Detection Logic

### Method 1: MD5 Hash (Primary)
```python
KNOWN_PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

def is_placeholder_by_hash(filepath):
    with open(filepath, 'rb') as f:
        file_md5 = hashlib.md5(f.read()).hexdigest()
    return file_md5 == KNOWN_PLACEHOLDER_MD5
```

**Why MD5?** The "image not available" placeholder from Google Books always has the same MD5 hash. This is the most reliable detection method.

### Method 2: File Size (REMOVED - DO NOT USE)
```python
# ❌ WRONG - Some real covers are small
if file_size < 10000:  # BAD LOGIC
    return True

# Example: "7 Powers" real cover = 8,985 bytes
# This would be incorrectly rejected!
```

**Never use file size alone** - legitimate book covers can be small.

### Method 3: Visual Inspection (Future Enhancement)
```python
# Use Claude API to visually check the image
def is_placeholder_by_vision(filepath):
    # Read image and send to Claude API
    # Ask: "Does this image contain the text 'image not available'?"
    # Return True/False
```

This catches new placeholder variants we haven't seen before.

## Complete Flow (Sequential)

```
FOR each book in CSV:

    FOR each strategy in ["exact", "title_only", "loose"]:

        1. Call Google Books API with strategy query
        2. Get up to 5 results (book IDs)
        3. Score each result by title/author similarity
        4. Sort results by score (highest first)

        FOR each book_id in sorted results:

            5. Extract imageLinks from API response
            6. Select best image URL using priority hierarchy:
               - Try "large" first
               - Then "medium"
               - Then "smallThumbnail" ✅ (usually works)
               - Finally "thumbnail"

            7. Download image to local file
            8. Calculate MD5 hash of downloaded file

            9. IF md5 == KNOWN_PLACEHOLDER_MD5:
                   Log attempt as "placeholder detected"
                   Continue to next book_id
               ELSE:
                   Log attempt as "success"
                   STOP - This book is done! ✅
                   BREAK out of all loops for this book

        10. Wait 1 second (rate limiting between strategies)

        11. IF real cover found:
                BREAK - Don't try remaining strategies

    12. IF no real cover found after all strategies:
            Log final failure

    13. Wait 2 seconds before next book (rate limiting)
```

## Logging Strategy

Every attempt is logged to `book_image_retrieval_log.csv`:

```csv
timestamp,book_title,book_author,strategy_name,strategy_number,book_id,
api_url,image_url,download_attempted,download_success,file_path,
file_size_bytes,md5_hash,is_placeholder,error_message,match_score,final_success
```

**Key Fields:**
- `final_success`: Only True when real cover found and saved
- `is_placeholder`: True when MD5 matches known placeholder
- `match_score`: Similarity score (0-1) between search and result
- `error_message`: Details about failures (503 errors, placeholders, etc.)

## Rate Limiting

**Between strategies:** 1 second delay
- Prevents hitting Google's rate limits
- Only occurs if previous strategy failed

**Between books:** 2 seconds delay
- Spreads requests over time
- Reduces chance of 503 errors

**On 503 errors:** Consider exponential backoff (future enhancement)

## Expected Results

Based on testing with 467 books:

- **First pass** (enrich_images.py): ~90% success (417/467 books)
- **Second pass** (retry with improved logic): ~93% of remaining (41/50 books)
- **Overall success rate:** ~98% (458/467 books)

**Remaining failures:** Usually books not in Google Books database or only available with restricted access.

## Code Structure

```python
# Configuration
GOOGLE_BOOKS_API_KEY = "..."
KNOWN_PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

# Helper functions
def similar(a, b) -> float
def search_google_books(title, author, strategy) -> list[(url, score, book_id)]
def download_image(url, filepath) -> bool
def is_placeholder(filepath) -> bool
def log_attempt(...) -> None

# Main processing
def process_single_book(title, author) -> bool
def process_all_books(csv_path) -> dict

# Entry point
if __name__ == "__main__":
    main()
```

## Version History

- **v1.0** (enrich_images.py): Basic download, used thumbnail only
- **v2.0** (retry_missing_images.py): Multiple strategies, still used thumbnail
- **v3.0** (retry_missing_images_with_logging.py): Prioritize smallThumbnail, comprehensive logging ✅
- **v4.0** (download_book_covers.py): Consolidated script with all improvements

## References

- Google Books API: https://developers.google.com/books/docs/v1/using
- MD5 hash of known placeholder: c96309220b9cbd205c36d879d09a3647
- Success rate analysis: IMAGE_RETRIEVAL_SUMMARY.md
