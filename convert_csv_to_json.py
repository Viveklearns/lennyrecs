#!/usr/bin/env python3
"""Convert CSV to JSON for frontend with comprehensive metadata."""

import csv
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations-enriched.csv"
MOVIES_METADATA_CSV = BASE_DIR / "movies_metadata.csv"
TV_METADATA_CSV = BASE_DIR / "tv_shows_metadata.csv"
OUTPUT_JSON = BASE_DIR / "recommendations.json"

def main():
    # Read metadata CSVs if they exist
    movies_metadata = {}
    tv_metadata = {}

    if MOVIES_METADATA_CSV.exists():
        with open(MOVIES_METADATA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                movies_metadata[row['title']] = row

    if TV_METADATA_CSV.exists():
        with open(TV_METADATA_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tv_metadata[row['title']] = row

    # Read CSV
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group by category and count recommendations
    books_count = defaultdict(int)
    movies_count = defaultdict(int)
    tv_count = defaultdict(int)

    books_data = defaultdict(lambda: {
        "title": "",
        "author": "",
        "recommendations": [],
        "cover": "N/A",
        "count": 0,
        "category": "N/A",
        "isbn_13": "N/A"
    })

    movies_data = defaultdict(lambda: {
        "title": "",
        "recommendations": [],
        "cover": "N/A",
        "count": 0
    })

    tv_data = defaultdict(lambda: {
        "title": "",
        "recommendations": [],
        "cover": "N/A",
        "count": 0
    })

    for row in rows:
        category = row["Category"]
        title = row["Title"].strip()  # Normalize whitespace

        if category == "Book":
            books_count[title] += 1
            books_data[title]["title"] = title
            books_data[title]["author"] = row["Author"]
            books_data[title]["count"] = books_count[title]
            books_data[title]["recommendations"].append({
                "guest": row["Guest"],
                "episode": row["Episode"],
                "description": row["Description"]
            })
            if row["Image_URL"] != "N/A":
                books_data[title]["cover"] = row["Image_URL"]
            # Add enriched metadata
            if "Google_Category" in row and row["Google_Category"] != "N/A":
                books_data[title]["category"] = row["Google_Category"]
            if "ISBN_13" in row and row["ISBN_13"] != "N/A":
                books_data[title]["isbn_13"] = row["ISBN_13"]

        elif category == "Movie":
            movies_count[title] += 1
            movies_data[title]["title"] = title
            movies_data[title]["count"] = movies_count[title]
            movies_data[title]["recommendations"].append({
                "guest": row["Guest"],
                "episode": row["Episode"],
                "description": row["Description"]
            })
            if row["Image_URL"] != "N/A":
                movies_data[title]["cover"] = row["Image_URL"]

            # Add metadata if available
            if title in movies_metadata:
                meta = movies_metadata[title]
                movies_data[title]["genres"] = meta.get("genres", "N/A")
                movies_data[title]["runtime"] = meta.get("runtime_minutes", "N/A")
                movies_data[title]["release_date"] = meta.get("release_date", "N/A")
                movies_data[title]["rating"] = meta.get("vote_average", "N/A")
                movies_data[title]["tmdb_url"] = meta.get("tmdb_url", "N/A")
                movies_data[title]["overview"] = meta.get("overview", "N/A")

        elif category == "TV Show":
            tv_count[title] += 1
            tv_data[title]["title"] = title
            tv_data[title]["count"] = tv_count[title]
            tv_data[title]["recommendations"].append({
                "guest": row["Guest"],
                "episode": row["Episode"],
                "description": row["Description"]
            })
            if row["Image_URL"] != "N/A":
                tv_data[title]["cover"] = row["Image_URL"]

            # Add metadata if available
            if title in tv_metadata:
                meta = tv_metadata[title]
                tv_data[title]["genres"] = meta.get("genres", "N/A")
                tv_data[title]["seasons"] = meta.get("number_of_seasons", "N/A")
                tv_data[title]["episodes"] = meta.get("number_of_episodes", "N/A")
                tv_data[title]["episode_runtime"] = meta.get("episode_runtime_avg", "N/A")
                tv_data[title]["first_air_date"] = meta.get("first_air_date", "N/A")
                tv_data[title]["status"] = meta.get("status", "N/A")
                tv_data[title]["rating"] = meta.get("vote_average", "N/A")
                tv_data[title]["tmdb_url"] = meta.get("tmdb_url", "N/A")
                tv_data[title]["overview"] = meta.get("overview", "N/A")

    # Convert to lists and sort by recommendation count
    books = sorted(books_data.values(), key=lambda x: x["count"], reverse=True)
    movies = sorted(movies_data.values(), key=lambda x: x["count"], reverse=True)
    tv_shows = sorted(tv_data.values(), key=lambda x: x["count"], reverse=True)

    # Create output
    output = {
        "books": books,
        "movies": movies,
        "tv_shows": tv_shows,
        "stats": {
            "total_books": len(books),
            "total_movies": len(movies),
            "total_tv_shows": len(tv_shows),
            "total_recommendations": len(rows)
        }
    }

    # Write JSON
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Created {OUTPUT_JSON}")
    print(f"   Books: {len(books)}")
    print(f"   Movies: {len(movies)}")
    print(f"   TV Shows: {len(tv_shows)}")

if __name__ == "__main__":
    main()
