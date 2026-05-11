#!/usr/bin/env python3
"""
Enrich movie/TV recommendations with comprehensive metadata from TMDB.
Creates detailed CSV databases with all available TMDB fields.
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
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations-enriched.csv"
OUTPUT_CSV = BASE_DIR / "extracted" / "all-recommendations-enriched.csv"
MOVIES_METADATA_CSV = BASE_DIR / "movies_metadata.csv"
TV_METADATA_CSV = BASE_DIR / "tv_shows_metadata.csv"
IMAGES_DIR = BASE_DIR / "images"

# Create images directory structure
(IMAGES_DIR / "movies").mkdir(parents=True, exist_ok=True)
(IMAGES_DIR / "tv").mkdir(parents=True, exist_ok=True)

# TMDB API Configuration
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search"
TMDB_MOVIE_DETAILS_URL = "https://api.themoviedb.org/3/movie"
TMDB_TV_DETAILS_URL = "https://api.themoviedb.org/3/tv"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def get_tmdb_metadata(title, media_type="movie"):
    """
    Get comprehensive metadata from TMDB API.

    Returns dict with all available fields or None if not found.
    """
    try:
        # Step 1: Search for the title
        endpoint = "movie" if media_type == "Movie" else "tv"
        search_url = f"{TMDB_SEARCH_URL}/{endpoint}"

        params = {
            "api_key": TMDB_API_KEY,
            "query": title
        }

        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "results" not in data or len(data["results"]) == 0:
            return None

        # Get the first result
        search_result = data["results"][0]
        tmdb_id = search_result["id"]

        # Step 2: Get detailed information
        details_url = f"{TMDB_MOVIE_DETAILS_URL}/{tmdb_id}" if media_type == "Movie" else f"{TMDB_TV_DETAILS_URL}/{tmdb_id}"

        details_response = requests.get(f"{details_url}?api_key={TMDB_API_KEY}", timeout=10)
        details_response.raise_for_status()
        details = details_response.json()

        # Extract poster URL
        poster_url = f"{TMDB_IMAGE_BASE}{details['poster_path']}" if details.get('poster_path') else None

        # Build metadata dict based on media type
        if media_type == "Movie":
            metadata = {
                'tmdb_id': tmdb_id,
                'imdb_id': details.get('imdb_id', 'N/A'),
                'genres': ', '.join([g['name'] for g in details.get('genres', [])]),
                'runtime_minutes': details.get('runtime', 'N/A'),
                'release_date': details.get('release_date', 'N/A'),
                'overview': details.get('overview', '').replace('\n', ' ').replace('\r', ' '),
                'vote_average': details.get('vote_average', 'N/A'),
                'vote_count': details.get('vote_count', 'N/A'),
                'homepage': details.get('homepage', 'N/A'),
                'tmdb_url': f"https://www.themoviedb.org/movie/{tmdb_id}",
                'poster_url': poster_url or 'N/A'
            }
        else:  # TV Show
            # Calculate average episode runtime
            episode_runtimes = details.get('episode_run_time', [])
            avg_runtime = sum(episode_runtimes) / len(episode_runtimes) if episode_runtimes else 'N/A'

            metadata = {
                'tmdb_id': tmdb_id,
                'genres': ', '.join([g['name'] for g in details.get('genres', [])]),
                'number_of_seasons': details.get('number_of_seasons', 'N/A'),
                'number_of_episodes': details.get('number_of_episodes', 'N/A'),
                'episode_runtime_avg': round(avg_runtime) if isinstance(avg_runtime, float) else avg_runtime,
                'first_air_date': details.get('first_air_date', 'N/A'),
                'last_air_date': details.get('last_air_date', 'N/A'),
                'status': details.get('status', 'N/A'),
                'overview': details.get('overview', '').replace('\n', ' ').replace('\r', ' '),
                'vote_average': details.get('vote_average', 'N/A'),
                'vote_count': details.get('vote_count', 'N/A'),
                'homepage': details.get('homepage', 'N/A'),
                'tmdb_url': f"https://www.themoviedb.org/tv/{tmdb_id}",
                'poster_url': poster_url or 'N/A'
            }

        return metadata

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
    fieldnames = None
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} recommendations")
    print()

    # Get unique movies/TV shows
    seen_titles = {}
    for row in rows:
        if row["Category"] in ["Movie", "TV Show"]:
            title = row["Title"].strip()
            key = (title, row["Category"])
            if key not in seen_titles:
                seen_titles[key] = row

    unique_media = list(seen_titles.values())
    print(f"Processing {len(unique_media)} unique movies/TV shows")
    print()

    # Process media
    print("Processing Movies/TV Shows:")
    print("-" * 70)
    media_results = []
    title_to_url = {}  # Map title to poster URL

    for i, item in enumerate(unique_media, 1):
        title = item["Title"].strip()
        category = item["Category"]
        print(f"[{i}/{len(unique_media)}] {title} ({category})")

        # Get poster URL from TMDB
        poster_url = get_movie_poster_tmdb(title, category)

        if poster_url:
            print(f"  ✓ Found poster: {poster_url[:60]}...")

            # Download image
            folder = "movies" if category == "Movie" else "tv"
            filename = f"{title[:50].replace('/', '-').replace(':', '')}.jpg"
            filepath = IMAGES_DIR / folder / filename

            if download_image(poster_url, filepath):
                print(f"  ✓ Downloaded to: images/{folder}/{filename}")
                title_to_url[(title, category)] = poster_url
                media_results.append({
                    "title": title,
                    "type": category,
                    "url": poster_url,
                    "local_path": f"images/{folder}/{filename}"
                })
            else:
                title_to_url[(title, category)] = "N/A"
        else:
            print(f"  ✗ No poster found")
            title_to_url[(title, category)] = "N/A"

        time.sleep(0.5)  # Rate limiting (TMDB allows 40 requests/10 seconds)

        # Progress update every 50 items
        if i % 50 == 0:
            print()
            print(f"📊 Progress: {i}/{len(unique_media)} processed, {len(media_results)} posters downloaded")
            print()

    # Update all rows with Image_URL
    for row in rows:
        if row["Category"] in ["Movie", "TV Show"]:
            title = row["Title"].strip()
            key = (title, row["Category"])
            if key in title_to_url:
                row["Image_URL"] = title_to_url[key]

    # Write updated CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print()
    print("=" * 70)
    print("✅ COMPLETE!")
    print(f"Movies/TV with posters: {len(media_results)}/{len(unique_media)}")
    print(f"Success rate: {len(media_results)*100//len(unique_media) if unique_media else 0}%")
    print()
    print("Images saved to:")
    print(f"  - {IMAGES_DIR}/movies/")
    print(f"  - {IMAGES_DIR}/tv/")
    print(f"\nCSV updated: {OUTPUT_CSV}")
    print("=" * 70)

if __name__ == "__main__":
    main()
