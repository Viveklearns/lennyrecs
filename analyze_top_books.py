#!/usr/bin/env python3
"""Analyze book recommendations to find the most recommended books."""

import csv
from collections import defaultdict
from pathlib import Path

# Configuration
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
INPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"

def main():
    # Read CSV
    rows = []
    with open(INPUT_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Group books by title
    books = defaultdict(list)

    for row in rows:
        if row["Category"] == "Book":
            title = row["Title"]
            books[title].append({
                "episode": row["Episode"],
                "guest": row["Guest"],
                "author": row["Author"],
                "description": row["Description"],
                "image_url": row["Image_URL"]
            })

    # Sort by frequency
    sorted_books = sorted(books.items(), key=lambda x: len(x[1]), reverse=True)

    print("=" * 70)
    print("Top Recommended Books from Lenny's Podcast")
    print("=" * 70)
    print()

    print("TOP 20 MOST RECOMMENDED BOOKS:")
    print("-" * 70)

    for i, (title, recommendations) in enumerate(sorted_books[:20], 1):
        count = len(recommendations)
        author = recommendations[0]["author"]

        print(f"\n{i}. {title}")
        print(f"   Author: {author}")
        print(f"   Recommended {count} times by:")

        for rec in recommendations:
            guest = rec["guest"]
            print(f"   - {guest}")

    print()
    print("=" * 70)
    print(f"Total unique books: {len(books)}")
    print(f"Books recommended 2+ times: {len([b for b in books.values() if len(b) >= 2])}")
    print(f"Books recommended 3+ times: {len([b for b in books.values() if len(b) >= 3])}")
    print("=" * 70)

if __name__ == "__main__":
    main()
