#!/usr/bin/env python3
"""
Retry fetching images for the 50 books that got placeholder images.
Uses improved search strategies with comprehensive logging to CSV database.
"""

import os
import requests
import time
import csv
import hashlib
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
IMAGES_DIR = BASE_DIR / "images" / "books"
LOG_FILE = BASE_DIR / "book_image_retrieval_log.csv"
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

# Placeholder checksum to identify
PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

# Books that still have placeholder images (after first run)
PLACEHOLDER_BOOKS = [
    ("7 Powers", "Hamilton Helmer"),
    ("15 Commitments of Conscious Leadership", "Jim Dethmer and Diana Chapman"),
    ("A Deepness in the Sky", "N/A"),
    ("Breakneck", "Dan Wang"),
    ("End of Average", "Todd Rose"),
    ("Founding Sales", "Pete Kazanjy"),
    ("Getting Real", "37 Signals"),
    ("It's Not How Good You Are, It's How Good You Want to Be", "Paul Arden"),
    ("Kindred", "Octavia Butler"),
    ("Le Ton beau de Marot", "Douglas Hofstadter"),
    ("Metabolical", "N/A"),
    ("Obviously Awesome", "April Dunford"),
    ("Orbiting the Giant Hairball: A Corporate Fool's Guide to Surviving with Grace", "Gordon MacKenzie"),
    ("Power: Why Some People Have It and Others Don't", "Jeffrey Pfeffer"),
    ("Radical Focus", "Christina Wodtke"),
    ("Range", "David Epstein"),
    ("Replacing Guilt", "Nate Soares"),
    ("Revolt of the Public", "N/A"),
    ("Simple Path to Wealth", "JL Collins"),
    ("Snuggle Puppy", "N/A"),
    ("Strong Product People", "Petra Wille"),
    ("The Case Against Reality", "Donald Hoffman"),
    ("The Elements of Thinking in Systems", "N/A"),
    ("Tress by the Emerald Sea", "Brandon Sanderson"),
]

# Initialize CSV log file
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

def log_attempt(book_title, book_author, strategy_name, strategy_number, book_id,
                api_url, image_url, download_attempted, download_success, file_path,
                file_size, md5_hash, is_placeholder, error_message, match_score, final_success):
    """Log a single attempt to the CSV file."""
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

def similar(a, b):
    """Check if two strings are similar (for title matching)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_google_books(title, author, strategy="default"):
    """Search Google Books with different strategies. Returns list of (url, score, book_id) tuples."""

    # Strategy 1: intitle: and inauthor:
    if strategy == "exact":
        if author and author != "N/A":
            query = f'intitle:"{title}" inauthor:"{author}"'
        else:
            query = f'intitle:"{title}"'

    # Strategy 2: Just title in quotes
    elif strategy == "title_only":
        query = f'intitle:"{title}"'

    # Strategy 3: Title without quotes + author
    elif strategy == "loose":
        query = f"{title}"
        if author and author != "N/A":
            query += f" {author}"

    # Default
    else:
        query = f"{title}"
        if author and author != "N/A":
            query += f" {author}"

    try:
        params = {
            "q": query,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 5  # Get top 5 to find best match
        }

        api_url = f"{GOOGLE_BOOKS_API}?q={requests.utils.quote(query)}&key={GOOGLE_BOOKS_API_KEY}&maxResults=5"

        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            # Collect ALL results with imageLinks, sorted by score
            results = []

            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                result_title = volume_info.get("title", "")
                result_authors = volume_info.get("authors", [])
                image_links = volume_info.get("imageLinks", {})
                book_id = item.get("id", "")

                # Skip if no image
                if not image_links:
                    continue

                # Score this result
                title_score = similar(title, result_title)

                # If we have an author, check author match too
                if author and author != "N/A" and result_authors:
                    author_str = " ".join(result_authors)
                    author_score = similar(author, author_str)
                    total_score = (title_score * 0.7) + (author_score * 0.3)
                else:
                    total_score = title_score

                # Only consider decent matches
                if total_score > 0.6:
                    # Get best quality image URL - prioritize smallThumbnail (zoom=5)
                    image_url = None
                    if "large" in image_links:
                        image_url = image_links["large"]
                    elif "medium" in image_links:
                        image_url = image_links["medium"]
                    elif "smallThumbnail" in image_links:
                        # smallThumbnail often has zoom=5 which works better
                        thumb = image_links["smallThumbnail"]
                        thumb = thumb.replace("http://", "https://")
                        image_url = thumb
                    elif "thumbnail" in image_links:
                        thumb = image_links["thumbnail"]
                        thumb = thumb.replace("http://", "https://")
                        thumb = thumb.replace("zoom=1", "zoom=2")
                        image_url = thumb

                    if image_url:
                        results.append((image_url, total_score, book_id, api_url))

            # Sort by score (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            return results

        return []

    except Exception as e:
        print(f"    Error: {e}")
        return []

def download_image(url, filepath):
    """Download image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"    Download error: {e}")
        return False

def main():
    print("=" * 70)
    print("Retrying 50 Books with Placeholder Images (WITH LOGGING)")
    print("=" * 70)
    print(f"\nLog file: {LOG_FILE}")
    print()

    # Initialize log file
    init_log_file()

    success_count = 0
    strategies = [("exact", 1), ("title_only", 2), ("loose", 3)]

    for i, (title, author) in enumerate(PLACEHOLDER_BOOKS, 1):
        print(f"[{i}/{len(PLACEHOLDER_BOOKS)}] {title}")
        print(f"    Author: {author}")

        # Prepare filepath upfront
        author_normalized = author.replace('/', '-')
        filename = f"{title}_{author_normalized}.jpg"
        filepath = IMAGES_DIR / filename

        # Collect all possible image URLs from all strategies
        all_results = []

        # Try strategies with delays between each
        for strategy_name, strategy_number in strategies:
            results = search_google_books(title, author, strategy_name)
            if results:
                for url, score, book_id, api_url in results:
                    all_results.append((url, score, strategy_name, strategy_number, book_id, api_url))

            # Wait 1 second between strategies to avoid rate limiting
            time.sleep(1)

        if all_results:
            # Sort by score (highest first)
            all_results.sort(key=lambda x: x[1], reverse=True)

            # Try each result until we find a non-placeholder
            downloaded = False

            for url, score, strategy_name, strategy_number, book_id, api_url in all_results:
                print(f"    Trying: score={score:.2f}, strategy={strategy_name}, book_id={book_id[:12]}...")

                download_attempted = True
                error_message = None

                if download_image(url, filepath):
                    download_success = True

                    # Check if it's a placeholder
                    with open(filepath, 'rb') as f:
                        file_md5 = hashlib.md5(f.read()).hexdigest()

                    file_size = filepath.stat().st_size

                    # Only check MD5 - file size can vary (some real covers are small)
                    if file_md5 == PLACEHOLDER_MD5:
                        is_placeholder = True
                        final_success = False
                        error_message = f"Placeholder detected (size: {file_size} bytes, md5: {file_md5[:8]}...)"
                        print(f"      ✗ {error_message}")

                        # Log this attempt
                        log_attempt(title, author, strategy_name, strategy_number, book_id,
                                  api_url, url, download_attempted, download_success, str(filepath),
                                  file_size, file_md5, is_placeholder, error_message, score, final_success)
                        continue
                    else:
                        is_placeholder = False
                        final_success = True
                        print(f"      ✓ Real cover found! ({file_size} bytes)")

                        # Log successful attempt
                        log_attempt(title, author, strategy_name, strategy_number, book_id,
                                  api_url, url, download_attempted, download_success, str(filepath),
                                  file_size, file_md5, is_placeholder, None, score, final_success)

                        downloaded = True
                        success_count += 1
                        break
                else:
                    download_success = False
                    is_placeholder = False
                    final_success = False
                    error_message = "Download failed"
                    print(f"      ✗ Download failed, trying next...")

                    # Log failed download attempt
                    log_attempt(title, author, strategy_name, strategy_number, book_id,
                              api_url, url, download_attempted, download_success, str(filepath),
                              0, "", is_placeholder, error_message, score, final_success)

            if not downloaded:
                print(f"    ✗ All options exhausted - no real cover found")
                # Log final failure
                log_attempt(title, author, "all_strategies", 0, "",
                          "", "", False, False, str(filepath),
                          0, "", False, "All strategies exhausted", 0, False)
        else:
            print(f"    ✗ No match found")
            # Log no results
            log_attempt(title, author, "all_strategies", 0, "",
                      "", "", False, False, str(filepath),
                      0, "", False, "No API results found", 0, False)

        print()

        # Wait 2 seconds between books to avoid rate limiting
        time.sleep(2)

    print("=" * 70)
    print(f"✅ Complete: {success_count}/{len(PLACEHOLDER_BOOKS)} covers downloaded")
    print(f"Success rate: {success_count*100//len(PLACEHOLDER_BOOKS)}%")
    print(f"\n📊 Detailed log saved to: {LOG_FILE}")
    print("=" * 70)

if __name__ == "__main__":
    main()
