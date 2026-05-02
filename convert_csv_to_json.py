#!/usr/bin/env python3
"""Convert CSV to JSON for frontend."""

import csv
import json
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
OUTPUT_JSON = BASE_DIR / "recommendations.json"

def main():
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
        "count": 0
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
        title = row["Title"]

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
