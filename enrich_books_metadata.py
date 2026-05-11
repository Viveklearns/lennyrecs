#!/usr/bin/env python3
"""
Enrich book recommendations with metadata from Google Books API.

Adds:
- Category (from Google Books categories)
- ISBN-13 (if available)
- Updates image if missing (using improved strategy)

Test mode: Run on 5 books first before full dataset.
"""

import csv
import hashlib
import os
import requests
import time
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_DIR = Path(__file__).parent
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
OUTPUT_CSV = BASE_DIR / "extracted" / "all-recommendations-enriched.csv"
IMAGES_DIR = BASE_DIR / "images" / "books"

GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

# Known placeholder MD5 hash
KNOWN_PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

# Rate limiting - increased to avoid 503 errors
DELAY_BETWEEN_BOOKS = 3  # seconds (increased from 1.5 to avoid rate limits)

# Test mode - set to True to test with 5 books only
TEST_MODE = False  # Changed to False to run on all books
TEST_LIMIT = 5

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def similar(a, b):
    """Calculate similarity score between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_google_books_exact(title, author):
    """
    Search Google Books API using exact strategy.
    Returns: (book_data, match_score) or (None, 0)

    book_data contains: {
        'book_id': str,
        'category': str or None,
        'isbn_13': str or None,
        'image_url': str or None
    }
    """
    # Build exact query
    if author and author != "N/A":
        query = f'intitle:"{title}" inauthor:"{author}"'
    else:
        query = f'intitle:"{title}"'

    try:
        params = {
            "q": query,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 5
        }

        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" not in data:
            return None, 0

        # Find best matching book
        best_match = None
        best_score = 0

        for item in data["items"]:
            volume_info = item.get("volumeInfo", {})
            result_title = volume_info.get("title", "")
            result_authors = volume_info.get("authors", [])

            # Calculate match score
            title_score = similar(title, result_title)

            if author and author != "N/A" and result_authors:
                author_str = " ".join(result_authors)
                author_score = similar(author, author_str)
                total_score = (title_score * 0.7) + (author_score * 0.3)
            else:
                total_score = title_score

            # Only consider decent matches
            if total_score > 0.6 and total_score > best_score:
                best_score = total_score

                # Extract metadata
                book_id = item.get("id", "")

                # Get category (first one if multiple)
                categories = volume_info.get("categories", [])
                category = categories[0] if categories else None

                # Get ISBN-13
                isbn_13 = None
                industry_identifiers = volume_info.get("industryIdentifiers", [])
                for identifier in industry_identifiers:
                    if identifier.get("type") == "ISBN_13":
                        isbn_13 = identifier.get("identifier")
                        break

                # Get image URL (prioritize smallThumbnail)
                image_links = volume_info.get("imageLinks", {})
                image_url = None

                if "large" in image_links:
                    image_url = image_links["large"]
                elif "medium" in image_links:
                    image_url = image_links["medium"]
                elif "smallThumbnail" in image_links:
                    image_url = image_links["smallThumbnail"].replace("http://", "https://")
                elif "thumbnail" in image_links:
                    image_url = image_links["thumbnail"].replace("http://", "https://")

                best_match = {
                    'book_id': book_id,
                    'category': category,
                    'isbn_13': isbn_13,
                    'image_url': image_url
                }

        return best_match, best_score

    except requests.exceptions.RequestException as e:
        print(f"      API Error: {e}")
        return None, 0

def has_valid_image(title, author):
    """Check if book already has a valid (non-placeholder) image."""
    author_normalized = author.replace('/', '-')
    filename = f"{title}_{author_normalized}.jpg"
    filepath = IMAGES_DIR / filename

    if not filepath.exists():
        return False

    try:
        with open(filepath, 'rb') as f:
            file_md5 = hashlib.md5(f.read()).hexdigest()

        # Return True if NOT a placeholder
        return file_md5 != KNOWN_PLACEHOLDER_MD5
    except Exception:
        return False

def download_image(url, filepath):
    """Download image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"      Download failed: {e}")
        return False

# ============================================================================
# MAIN PROCESSING
# ============================================================================

def process_books():
    """Process books and enrich with metadata."""

    # Read CSV
    print(f"\n{'=' * 80}")
    print(f"BOOK METADATA ENRICHMENT")
    if TEST_MODE:
        print(f"TEST MODE: Processing only {TEST_LIMIT} books")
    print(f"{'=' * 80}\n")

    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Filter to books only
    books = [r for r in rows if r["Category"] == "Book"]

    # Get unique books
    seen = set()
    unique_books = []
    for book in books:
        key = (book["Title"], book["Author"])
        if key not in seen:
            seen.add(key)
            unique_books.append(book)

    print(f"Total unique books: {len(unique_books)}")

    if TEST_MODE:
        unique_books = unique_books[:TEST_LIMIT]
        print(f"Testing with first {len(unique_books)} books\n")

    # Add new fields to fieldnames if not present
    new_fieldnames = list(fieldnames)
    if 'Google_Category' not in new_fieldnames:
        new_fieldnames.append('Google_Category')
    if 'ISBN_13' not in new_fieldnames:
        new_fieldnames.append('ISBN_13')
    if 'Book_ID' not in new_fieldnames:
        new_fieldnames.append('Book_ID')

    # Process each book
    enriched_count = 0
    images_downloaded = 0

    for i, book in enumerate(unique_books, 1):
        title = book["Title"]
        author = book["Author"]

        print(f"[{i}/{len(unique_books)}] {title}")
        print(f"    Author: {author}")

        # Search Google Books
        book_data, score = search_google_books_exact(title, author)

        if book_data:
            print(f"    ✓ Found match (score: {score:.2f})")
            print(f"      Book ID: {book_data['book_id'][:20]}...")
            print(f"      Category: {book_data['category'] or 'N/A'}")
            print(f"      ISBN-13: {book_data['isbn_13'] or 'N/A'}")

            # Update book metadata
            book['Google_Category'] = book_data['category'] or 'N/A'
            book['ISBN_13'] = book_data['isbn_13'] or 'N/A'
            book['Book_ID'] = book_data['book_id']

            enriched_count += 1

            # Check if we need to download image
            if book_data['image_url'] and not has_valid_image(title, author):
                print(f"      Image missing/placeholder - downloading...")

                author_normalized = author.replace('/', '-')
                filename = f"{title}_{author_normalized}.jpg"
                filepath = IMAGES_DIR / filename

                if download_image(book_data['image_url'], filepath):
                    # Verify not a placeholder
                    file_md5 = hashlib.md5(filepath.read_bytes()).hexdigest()
                    if file_md5 != KNOWN_PLACEHOLDER_MD5:
                        file_size = filepath.stat().st_size
                        print(f"      ✓ Image downloaded ({file_size} bytes)")
                        images_downloaded += 1
                    else:
                        print(f"      ✗ Downloaded placeholder image")
            else:
                print(f"      Image already exists")
        else:
            print(f"    ✗ No match found")
            book['Google_Category'] = 'N/A'
            book['ISBN_13'] = 'N/A'
            book['Book_ID'] = 'N/A'

        print()

        # Rate limiting
        if i < len(unique_books):
            time.sleep(DELAY_BETWEEN_BOOKS)

    # Update all rows with enriched data
    book_dict = {(b['Title'], b['Author']): b for b in unique_books}

    for row in rows:
        if row["Category"] == "Book":
            key = (row["Title"], row["Author"])
            if key in book_dict:
                enriched_book = book_dict[key]
                row['Google_Category'] = enriched_book.get('Google_Category', 'N/A')
                row['ISBN_13'] = enriched_book.get('ISBN_13', 'N/A')
                row['Book_ID'] = enriched_book.get('Book_ID', 'N/A')
            else:
                row['Google_Category'] = 'N/A'
                row['ISBN_13'] = 'N/A'
                row['Book_ID'] = 'N/A'
        else:
            # Non-books get N/A
            row['Google_Category'] = 'N/A'
            row['ISBN_13'] = 'N/A'
            row['Book_ID'] = 'N/A'

    # Write output CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=new_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print(f"{'=' * 80}")
    print(f"✅ Complete!")
    print(f"   Books enriched: {enriched_count}/{len(unique_books)}")
    print(f"   Images downloaded: {images_downloaded}")
    print(f"\nOutput saved to: {OUTPUT_CSV}")
    print(f"{'=' * 80}\n")

if __name__ == "__main__":
    process_books()
