#!/usr/bin/env python3
"""
Enrich movie/TV recommendations with comprehensive metadata from TMDB.
Creates detailed CSV databases with all available TMDB fields.

V2 - Comprehensive metadata extraction
"""

import csv
import json
import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path(__file__).parent
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
    Makes 2 API calls: search + details.

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
                'genres': ', '.join([g['name'] for g in details.get('genres', [])]) or 'N/A',
                'runtime_minutes': details.get('runtime', 'N/A'),
                'release_date': details.get('release_date', 'N/A'),
                'overview': details.get('overview', '').replace('\n', ' ').replace('\r', ' ')[:500],  # Limit length
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
                'genres': ', '.join([g['name'] for g in details.get('genres', [])]) or 'N/A',
                'number_of_seasons': details.get('number_of_seasons', 'N/A'),
                'number_of_episodes': details.get('number_of_episodes', 'N/A'),
                'episode_runtime_avg': round(avg_runtime) if isinstance(avg_runtime, float) else avg_runtime,
                'first_air_date': details.get('first_air_date', 'N/A'),
                'last_air_date': details.get('last_air_date', 'N/A'),
                'status': details.get('status', 'N/A'),
                'overview': details.get('overview', '').replace('\n', ' ').replace('\r', ' ')[:500],
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
        return False

def main():
    print("=" * 80)
    print("COMPREHENSIVE MOVIE/TV METADATA ENRICHMENT - V2")
    print("=" * 80)
    print()

    # Read CSV and count recommendations
    rows = []
    fieldnames = None
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    print(f"Loaded {len(rows)} recommendations")

    # Get unique movies/TV shows and count recommendations
    movie_counts = defaultdict(int)
    tv_counts = defaultdict(int)
    seen_titles = {}

    for row in rows:
        if row["Category"] in ["Movie", "TV Show"]:
            title = row["Title"].strip()
            category = row["Category"]
            key = (title, category)

            if category == "Movie":
                movie_counts[title] += 1
            else:
                tv_counts[title] += 1

            if key not in seen_titles:
                seen_titles[key] = row

    unique_media = list(seen_titles.values())
    unique_movies = [m for m in unique_media if m["Category"] == "Movie"]
    unique_tv = [m for m in unique_media if m["Category"] == "TV Show"]

    print(f"Unique movies: {len(unique_movies)}")
    print(f"Unique TV shows: {len(unique_tv)}")
    print()

    # Process movies
    print("=" * 80)
    print("MOVIES")
    print("=" * 80)

    movies_data = []
    title_to_url = {}

    for i, item in enumerate(unique_movies, 1):
        title = item["Title"].strip()
        print(f"[{i}/{len(unique_movies)}] {title}")

        # Get comprehensive metadata
        metadata = get_tmdb_metadata(title, "Movie")

        if metadata:
            print(f"  ✓ Found: {metadata['genres']} | {metadata['runtime_minutes']} min | {metadata['release_date']}")

            # Download poster
            if metadata['poster_url'] != 'N/A':
                filename = f"{title[:50].replace('/', '-').replace(':', '')}.jpg"
                filepath = IMAGES_DIR / "movies" / filename
                local_path = f"images/movies/{filename}"

                if download_image(metadata['poster_url'], filepath):
                    print(f"  ✓ Downloaded poster")
                else:
                    local_path = "N/A"
            else:
                local_path = "N/A"

            # Add to movies data
            movies_data.append({
                'title': title,
                'tmdb_id': metadata['tmdb_id'],
                'imdb_id': metadata['imdb_id'],
                'category': 'Movie',
                'genres': metadata['genres'],
                'runtime_minutes': metadata['runtime_minutes'],
                'release_date': metadata['release_date'],
                'overview': metadata['overview'],
                'vote_average': metadata['vote_average'],
                'vote_count': metadata['vote_count'],
                'homepage': metadata['homepage'],
                'tmdb_url': metadata['tmdb_url'],
                'poster_url': metadata['poster_url'],
                'local_poster_path': local_path,
                'recommendation_count': movie_counts[title]
            })

            title_to_url[(title, "Movie")] = metadata['poster_url']

        else:
            print(f"  ✗ Not found in TMDB")
            title_to_url[(title, "Movie")] = "N/A"

        time.sleep(1)  # Rate limiting: 2 API calls per movie

    # Process TV shows
    print()
    print("=" * 80)
    print("TV SHOWS")
    print("=" * 80)

    tv_data = []

    for i, item in enumerate(unique_tv, 1):
        title = item["Title"].strip()
        print(f"[{i}/{len(unique_tv)}] {title}")

        # Get comprehensive metadata
        metadata = get_tmdb_metadata(title, "TV Show")

        if metadata:
            print(f"  ✓ Found: {metadata['genres']} | {metadata['number_of_seasons']} seasons | {metadata['number_of_episodes']} episodes")

            # Download poster
            if metadata['poster_url'] != 'N/A':
                filename = f"{title[:50].replace('/', '-').replace(':', '')}.jpg"
                filepath = IMAGES_DIR / "tv" / filename
                local_path = f"images/tv/{filename}"

                if download_image(metadata['poster_url'], filepath):
                    print(f"  ✓ Downloaded poster")
                else:
                    local_path = "N/A"
            else:
                local_path = "N/A"

            # Add to TV data
            tv_data.append({
                'title': title,
                'tmdb_id': metadata['tmdb_id'],
                'category': 'TV Show',
                'genres': metadata['genres'],
                'number_of_seasons': metadata['number_of_seasons'],
                'number_of_episodes': metadata['number_of_episodes'],
                'episode_runtime_avg': metadata['episode_runtime_avg'],
                'first_air_date': metadata['first_air_date'],
                'last_air_date': metadata['last_air_date'],
                'status': metadata['status'],
                'overview': metadata['overview'],
                'vote_average': metadata['vote_average'],
                'vote_count': metadata['vote_count'],
                'homepage': metadata['homepage'],
                'tmdb_url': metadata['tmdb_url'],
                'poster_url': metadata['poster_url'],
                'local_poster_path': local_path,
                'recommendation_count': tv_counts[title]
            })

            title_to_url[(title, "TV Show")] = metadata['poster_url']

        else:
            print(f"  ✗ Not found in TMDB")
            title_to_url[(title, "TV Show")] = "N/A"

        time.sleep(1)  # Rate limiting

    # Write movies metadata CSV
    if movies_data:
        with open(MOVIES_METADATA_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=movies_data[0].keys())
            writer.writeheader()
            writer.writerows(movies_data)

    # Write TV shows metadata CSV
    if tv_data:
        with open(TV_METADATA_CSV, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=tv_data[0].keys())
            writer.writeheader()
            writer.writerows(tv_data)

    # Update main CSV with Image_URL
    for row in rows:
        if row["Category"] in ["Movie", "TV Show"]:
            title = row["Title"].strip()
            key = (title, row["Category"])
            if key in title_to_url:
                row["Image_URL"] = title_to_url[key]

    # Write updated main CSV
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    print()
    print("=" * 80)
    print("✅ COMPLETE!")
    print(f"   Movies enriched: {len(movies_data)}/{len(unique_movies)}")
    print(f"   TV shows enriched: {len(tv_data)}/{len(unique_tv)}")
    print()
    print("📊 Output files:")
    print(f"   Movies metadata: {MOVIES_METADATA_CSV}")
    print(f"   TV shows metadata: {TV_METADATA_CSV}")
    print(f"   Main CSV updated: {OUTPUT_CSV}")
    print("=" * 80)

if __name__ == "__main__":
    main()
