#!/usr/bin/env python3
"""
Book Cover Image Downloader v4.0 - Consolidated Version
========================================================

Complete solution for downloading book cover images from Google Books API
with comprehensive logging and placeholder detection.

This script consolidates and improves upon:
- enrich_images.py (v1.0)
- retry_missing_images.py (v2.0)
- retry_missing_images_with_logging.py (v3.0)

Key improvements in v4.0:
- Prioritizes smallThumbnail (zoom=5) for best results
- Sequential strategy testing (stops on first success)
- MD5-based placeholder detection (no file size check)
- Comprehensive CSV logging of all attempts
- Proper rate limiting to avoid 503 errors

See BOOK_IMAGE_DOWNLOAD_LOGIC.md for complete logic documentation.

Usage:
    python3 download_book_covers.py

Requirements:
    pip install requests

Author: Generated with Claude Code (claude-sonnet-4-5-20250929)
Date: 2026-05-02
"""

import csv
import hashlib
import os
import requests
import time
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
IMAGES_DIR = BASE_DIR / "images" / "books"
LOG_FILE = BASE_DIR / "book_cover_download_log.csv"

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

# Known placeholder MD5 hash
KNOWN_PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

# Rate limiting delays (seconds)
DELAY_BETWEEN_STRATEGIES = 1
DELAY_BETWEEN_BOOKS = 2

# Search strategies (in priority order)
STRATEGIES = [
    ("exact", 1),       # intitle:"Title" inauthor:"Author"
    ("title_only", 2),  # intitle:"Title"
    ("loose", 3)        # Title Author (no operators)
]

# ============================================================================
# LOGGING
# ============================================================================

def init_log_file():
    """Create CSV log file with headers if it doesn't exist."""
    if not LOG_FILE.exists():
        with open(LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'timestamp',
                'book_title',
                'book_author',
                'strategy_name',
                'strategy_number',
                'book_id',
                'api_url',
                'image_url',
                'download_attempted',
                'download_success',
                'file_path',
                'file_size_bytes',
                'md5_hash',
                'is_placeholder',
                'error_message',
                'match_score',
                'final_success'
            ])
        print(f"📋 Created log file: {LOG_FILE}")

def log_attempt(book_title, book_author, strategy_name, strategy_number, book_id,
                api_url, image_url, download_attempted, download_success, file_path,
                file_size, md5_hash, is_placeholder, error_message, match_score, final_success):
    """Log a single download attempt to CSV."""
    with open(LOG_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().isoformat(),
            book_title,
            book_author,
            strategy_name,
            strategy_number,
            book_id,
            api_url,
            image_url,
            download_attempted,
            download_success,
            file_path,
            file_size,
            md5_hash,
            is_placeholder,
            error_message,
            match_score,
            final_success
        ])

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def similar(a, b):
    """
    Calculate similarity score between two strings (0.0 to 1.0).
    Used for matching search results to original title/author.
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def build_search_query(title, author, strategy):
    """
    Build Google Books API search query based on strategy.

    Strategy "exact":     intitle:"Title" inauthor:"Author"
    Strategy "title_only": intitle:"Title"
    Strategy "loose":     Title Author (no operators)
    """
    if strategy == "exact":
        if author and author != "N/A":
            return f'intitle:"{title}" inauthor:"{author}"'
        else:
            return f'intitle:"{title}"'

    elif strategy == "title_only":
        return f'intitle:"{title}"'

    elif strategy == "loose":
        if author and author != "N/A":
            return f"{title} {author}"
        else:
            return title

    else:
        # Default: same as loose
        return f"{title} {author}" if author and author != "N/A" else title

def search_google_books(title, author, strategy):
    """
    Search Google Books API and return list of (image_url, match_score, book_id, api_url) tuples.
    Returns results sorted by match score (highest first).
    """
    query = build_search_query(title, author, strategy)

    try:
        params = {
            "q": query,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 5  # Get top 5 results per strategy
        }

        # Construct API URL for logging
        api_url = f"{GOOGLE_BOOKS_API}?q={requests.utils.quote(query)}&key={GOOGLE_BOOKS_API_KEY}&maxResults=5"

        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            return []

        results = []

        for item in data["items"]:
            volume_info = item.get("volumeInfo", {})
            result_title = volume_info.get("title", "")
            result_authors = volume_info.get("authors", [])
            image_links = volume_info.get("imageLinks", {})
            book_id = item.get("id", "")

            # Skip if no images available
            if not image_links:
                continue

            # Calculate match score
            title_score = similar(title, result_title)

            if author and author != "N/A" and result_authors:
                author_str = " ".join(result_authors)
                author_score = similar(author, author_str)
                total_score = (title_score * 0.7) + (author_score * 0.3)
            else:
                total_score = title_score

            # Only consider decent matches (>60% similarity)
            if total_score <= 0.6:
                continue

            # Select best image URL using priority hierarchy
            # Priority: large > medium > smallThumbnail > thumbnail
            image_url = None

            if "large" in image_links:
                image_url = image_links["large"]
            elif "medium" in image_links:
                image_url = image_links["medium"]
            elif "smallThumbnail" in image_links:
                # ✅ KEY FIX: smallThumbnail (zoom=5) works best!
                image_url = image_links["smallThumbnail"]
                image_url = image_url.replace("http://", "https://")
            elif "thumbnail" in image_links:
                image_url = image_links["thumbnail"]
                image_url = image_url.replace("http://", "https://")
                # Note: Don't change zoom parameter for thumbnail

            if image_url:
                results.append((image_url, total_score, book_id, api_url))

        # Sort by score (highest first)
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  API Error: {e}")
        return []

def download_image(url, filepath):
    """Download image from URL to local file. Returns True if successful."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except requests.exceptions.RequestException as e:
        print(f"    ⚠️  Download failed: {e}")
        return False

def is_placeholder(filepath):
    """
    Check if downloaded image is a placeholder by comparing MD5 hash.

    DO NOT use file size check - some real covers are small!
    Example: "7 Powers" real cover = 8,985 bytes
    """
    try:
        with open(filepath, 'rb') as f:
            file_md5 = hashlib.md5(f.read()).hexdigest()
        return file_md5 == KNOWN_PLACEHOLDER_MD5
    except Exception:
        return False

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_single_book(title, author):
    """
    Download cover image for a single book using sequential strategy testing.
    Returns True if successful, False otherwise.

    Logic:
    1. Try Strategy 1 "exact"
       - Get up to 5 book IDs sorted by match score
       - Try each book ID until real cover found
    2. If failed, wait 1s and try Strategy 2 "title_only"
    3. If failed, wait 1s and try Strategy 3 "loose"
    4. If all failed, return False
    """
    print(f"\n📖 {title}")
    print(f"    Author: {author}")

    # Prepare file path
    author_normalized = author.replace('/', '-')
    filename = f"{title}_{author_normalized}.jpg"
    filepath = IMAGES_DIR / filename

    # Try each strategy sequentially
    for strategy_name, strategy_number in STRATEGIES:
        print(f"    🔍 Strategy {strategy_number}: {strategy_name}")

        # Search Google Books
        results = search_google_books(title, author, strategy_name)

        if not results:
            print(f"       No results found")
            continue

        # Try each book ID (sorted by match score)
        for image_url, match_score, book_id, api_url in results:
            print(f"       Trying book_id={book_id[:12]}... (score={match_score:.2f})")

            # Download image
            if not download_image(image_url, filepath):
                log_attempt(title, author, strategy_name, strategy_number, book_id,
                          api_url, image_url, True, False, str(filepath),
                          0, "", False, "Download failed", match_score, False)
                continue

            # Check if placeholder
            file_size = filepath.stat().st_size
            file_md5 = hashlib.md5(filepath.read_bytes()).hexdigest()

            if is_placeholder(filepath):
                print(f"       ✗ Placeholder detected ({file_size} bytes)")
                log_attempt(title, author, strategy_name, strategy_number, book_id,
                          api_url, image_url, True, True, str(filepath),
                          file_size, file_md5, True, f"Placeholder (MD5: {file_md5[:8]}...)",
                          match_score, False)
                continue

            # Success! Real cover found
            print(f"       ✅ Real cover found! ({file_size} bytes)")
            log_attempt(title, author, strategy_name, strategy_number, book_id,
                      api_url, image_url, True, True, str(filepath),
                      file_size, file_md5, False, None, match_score, True)
            return True

        # Wait between strategies to avoid rate limiting
        if strategy_name != STRATEGIES[-1][0]:  # Don't wait after last strategy
            time.sleep(DELAY_BETWEEN_STRATEGIES)

    # All strategies failed
    print(f"    ❌ No real cover found after all strategies")
    log_attempt(title, author, "all_strategies", 0, "", "", "", False, False,
              str(filepath), 0, "", False, "All strategies exhausted", 0, False)
    return False

def process_all_books(csv_path):
    """
    Process all books from CSV file.
    Returns dict with statistics.
    """
    # Read books from CSV
    books = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Category"] == "Book":
                books.append((row["Title"], row["Author"]))

    # Remove duplicates (keep first occurrence)
    seen = set()
    unique_books = []
    for title, author in books:
        key = (title, author)
        if key not in seen:
            seen.add(key)
            unique_books.append((title, author))

    print(f"\n{'=' * 80}")
    print(f"BOOK COVER DOWNLOAD - v4.0 Consolidated")
    print(f"{'=' * 80}")
    print(f"Total unique books: {len(unique_books)}")
    print(f"Log file: {LOG_FILE}")
    print(f"{'=' * 80}\n")

    # Ensure directories exist
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    init_log_file()

    # Process each book
    success_count = 0
    for i, (title, author) in enumerate(unique_books, 1):
        print(f"\n[{i}/{len(unique_books)}]", end=" ")

        if process_single_book(title, author):
            success_count += 1

        # Wait between books
        if i < len(unique_books):
            time.sleep(DELAY_BETWEEN_BOOKS)

    # Summary
    print(f"\n{'=' * 80}")
    print(f"✅ Complete!")
    print(f"   Success: {success_count}/{len(unique_books)} ({success_count*100//len(unique_books)}%)")
    print(f"   Failed: {len(unique_books) - success_count}")
    print(f"\n📊 Detailed log: {LOG_FILE}")
    print(f"{'=' * 80}\n")

    return {
        "total": len(unique_books),
        "success": success_count,
        "failed": len(unique_books) - success_count,
        "success_rate": success_count / len(unique_books) if unique_books else 0
    }

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    if not INPUT_CSV.exists():
        print(f"❌ Error: Input CSV not found: {INPUT_CSV}")
        print(f"   Please run extract_all_with_api.py first to generate recommendations CSV")
        return 1

    try:
        stats = process_all_books(INPUT_CSV)
        return 0 if stats["success_rate"] > 0.9 else 1
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit(main())
