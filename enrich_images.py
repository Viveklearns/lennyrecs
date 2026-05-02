#!/usr/bin/env python3
"""
Enrich recommendations with cover images from Google Books API and TMDB.
Test with 10 books and 10 movies first.
"""

import csv
import json
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
OUTPUT_CSV = BASE_DIR / "extracted" / "all-recommendations-with-images.csv"
IMAGES_DIR = BASE_DIR / "images"

# Create images directory structure
(IMAGES_DIR / "books").mkdir(parents=True, exist_ok=True)
(IMAGES_DIR / "movies").mkdir(parents=True, exist_ok=True)
(IMAGES_DIR / "tv").mkdir(parents=True, exist_ok=True)

# API Configuration
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"
TMDB_API_KEY = "4b9613e7aeee43e3d5e17f5f4622b667"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def get_book_cover_google(title, author):
    """Get book cover URL from Google Books API."""
    try:
        # Build search query
        query = f"{title}"
        if author and author != "N/A":
            query += f" {author}"

        params = {
            "q": query,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 1
        }

        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" in data and len(data["items"]) > 0:
            item = data["items"][0]
            volume_info = item.get("volumeInfo", {})
            image_links = volume_info.get("imageLinks", {})

            # Try to get largest available image
            if "large" in image_links:
                return image_links["large"]
            elif "medium" in image_links:
                return image_links["medium"]
            elif "thumbnail" in image_links:
                # Replace http with https and upgrade to larger size
                thumb = image_links["thumbnail"]
                thumb = thumb.replace("http://", "https://")
                thumb = thumb.replace("zoom=1", "zoom=2")
                return thumb
            elif "smallThumbnail" in image_links:
                thumb = image_links["smallThumbnail"]
                thumb = thumb.replace("http://", "https://")
                return thumb

        return None

    except Exception as e:
        print(f"  ⚠️  Google Books API error: {e}")
        return None

def get_movie_poster_tmdb(title, media_type="movie"):
    """Get movie/TV poster URL from TMDB API."""
    if not TMDB_API_KEY:
        return None

    try:
        # Determine endpoint
        endpoint = "movie" if media_type == "Movie" else "tv"
        url = f"{TMDB_SEARCH_URL}/{endpoint}"

        params = {
            "api_key": TMDB_API_KEY,
            "query": title
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            poster_path = result.get("poster_path")

            if poster_path:
                return f"{TMDB_IMAGE_BASE}{poster_path}"

        return None

    except Exception as e:
        print(f"  ⚠️  TMDB API error: {e}")
        return None

def download_image(url, filepath):
    """Download image from URL to filepath."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"  ⚠️  Download error: {e}")
        return False

def main():
    print("=" * 70)
    print("Book Cover Image Enrichment - All Books")
    print("=" * 70)
    print()

    # Read CSV
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} recommendations")
    print()

    # Get ALL books
    books = [r for r in rows if r["Category"] == "Book"]
    print(f"Processing {len(books)} books")

    print()

    # Process books
    print("Processing Books:")
    print("-" * 70)
    book_results = []

    for i, book in enumerate(books, 1):
        title = book["Title"]
        author = book["Author"]
        print(f"[{i}/{len(books)}] {title} by {author}")

        # Get cover URL from Google Books
        cover_url = get_book_cover_google(title, author)

        if cover_url:
            print(f"  ✓ Found cover: {cover_url[:60]}...")

            # Download image
            filename = f"{title[:50].replace('/', '-')}_{author[:30].replace('/', '-')}.jpg"
            filepath = IMAGES_DIR / "books" / filename

            if download_image(cover_url, filepath):
                print(f"  ✓ Downloaded to: images/books/{filename}")
                book["Image_URL"] = cover_url
                book_results.append({
                    "title": title,
                    "author": author,
                    "url": cover_url,
                    "local_path": f"images/books/{filename}"
                })
            else:
                book["Image_URL"] = "N/A"
        else:
            print(f"  ✗ No cover found")
            book["Image_URL"] = "N/A"

        time.sleep(1)  # Rate limiting

        # Progress update every 50 books
        if i % 50 == 0:
            print()
            print(f"📊 Progress: {i}/{len(books)} processed, {len(book_results)} covers downloaded")
            print()

    # Summary
    print()
    print("=" * 70)
    print("✅ COMPLETE!")
    print(f"Books with covers: {len(book_results)}/{len(books)}")
    print(f"Success rate: {len(book_results)*100//len(books)}%")
    print()
    print("Images saved to:")
    print(f"  - {IMAGES_DIR}/books/")
    print("=" * 70)

if __name__ == "__main__":
    main()
