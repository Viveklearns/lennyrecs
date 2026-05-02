#!/usr/bin/env python3
"""
Enrich movie/TV recommendations with posters from TMDB.
"""

import csv
import json
import time
import requests
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
IMAGES_DIR = BASE_DIR / "images"

# Create images directory structure
(IMAGES_DIR / "movies").mkdir(parents=True, exist_ok=True)
(IMAGES_DIR / "tv").mkdir(parents=True, exist_ok=True)

# TMDB API Configuration
TMDB_API_KEY = "os.getenv("TMDB_API_KEY")"
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def get_movie_poster_tmdb(title, media_type="movie"):
    """Get movie/TV poster URL from TMDB API."""
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
    print("Movie/TV Poster Enrichment")
    print("=" * 70)
    print()

    # Read CSV
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Loaded {len(rows)} recommendations")
    print()

    # Get all movies/TV shows
    media = [r for r in rows if r["Category"] in ["Movie", "TV Show"]]
    print(f"Processing {len(media)} movies/TV shows")
    print()

    # Process media
    print("Processing Movies/TV Shows:")
    print("-" * 70)
    media_results = []

    for i, item in enumerate(media, 1):
        title = item["Title"]
        category = item["Category"]
        print(f"[{i}/{len(media)}] {title} ({category})")

        # Get poster URL from TMDB
        poster_url = get_movie_poster_tmdb(title, category)

        if poster_url:
            print(f"  ✓ Found poster: {poster_url[:60]}...")

            # Download image
            folder = "movies" if category == "Movie" else "tv"
            filename = f"{title[:50].replace('/', '-')}.jpg"
            filepath = IMAGES_DIR / folder / filename

            if download_image(poster_url, filepath):
                print(f"  ✓ Downloaded to: images/{folder}/{filename}")
                item["Image_URL"] = poster_url
                media_results.append({
                    "title": title,
                    "type": category,
                    "url": poster_url,
                    "local_path": f"images/{folder}/{filename}"
                })
            else:
                item["Image_URL"] = "N/A"
        else:
            print(f"  ✗ No poster found")
            item["Image_URL"] = "N/A"

        time.sleep(0.5)  # Rate limiting (TMDB allows 40 requests/10 seconds)

        # Progress update every 50 items
        if i % 50 == 0:
            print()
            print(f"📊 Progress: {i}/{len(media)} processed, {len(media_results)} posters downloaded")
            print()

    # Summary
    print()
    print("=" * 70)
    print("✅ COMPLETE!")
    print(f"Movies/TV with posters: {len(media_results)}/{len(media)}")
    print(f"Success rate: {len(media_results)*100//len(media)}%")
    print()
    print("Images saved to:")
    print(f"  - {IMAGES_DIR}/movies/")
    print(f"  - {IMAGES_DIR}/tv/")
    print("=" * 70)

if __name__ == "__main__":
    main()
