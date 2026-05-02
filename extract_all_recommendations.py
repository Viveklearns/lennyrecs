#!/usr/bin/env python3
"""
Extract all recommendations from Lenny's Podcast transcripts.
This script processes all 295 episodes and generates a master CSV file.
"""

import os
import json
import csv
import glob
import time
import re
from pathlib import Path

# Paths
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
PODCASTS_DIR = BASE_DIR / "03-podcasts"
OUTPUT_DIR = BASE_DIR / "extracted"
JSON_DIR = OUTPUT_DIR / "json"
CSV_DIR = OUTPUT_DIR / "csv"

# Create output directories
JSON_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

def extract_metadata(content):
    """Extract frontmatter metadata from markdown file."""
    metadata = {}

    # Find frontmatter between --- markers
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if not frontmatter_match:
        return metadata

    frontmatter = frontmatter_match.group(1)

    # Parse YAML-like frontmatter
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')

            # Handle arrays (tags)
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"') for v in value[1:-1].split(',')]

            metadata[key] = value

    return metadata

def extract_lightning_round(content):
    """Extract the lightning round section from transcript."""
    # Look for common lightning round markers
    patterns = [
        r'lightning round',
        r'very exciting lightning round',
        r'quick fire',
        r'rapid fire',
        r'favorite book',
        r'book.*recommend',
        r'favorite.*movie',
        r'favorite.*product'
    ]

    # Find the section
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            # Return everything from the match to the end
            return content[match.start():]

    # If no lightning round found, return last 3000 characters
    # (recommendations are usually at the end)
    return content[-3000:]

def extract_books_from_text(text, guest_name):
    """
    Extract book recommendations from text.
    This is a simplified extraction - in production, you'd use Claude API here.
    """
    books = []

    # Look for book recommendation patterns
    # This is a basic regex approach - Claude would be better
    book_patterns = [
        r'(?:book.*?recommend|favorite book|great book).*?[:\-\s]+(.*?)(?:by|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        r'([A-Z][^.!?]*(?:book|Book))\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    ]

    # Note: In production, this would call Claude API to properly extract
    # For now, returning empty array - Claude Code will fill this in
    return books

def process_episode(filepath):
    """Process a single episode file."""
    print(f"Processing: {filepath.name}")

    # Read the file
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    metadata = extract_metadata(content)

    if not metadata:
        print(f"  ⚠️  No metadata found, skipping...")
        return None

    # Extract lightning round section
    lightning_section = extract_lightning_round(content)

    # Create episode data structure
    episode_data = {
        "metadata": {
            "title": metadata.get("title", "Unknown"),
            "date": metadata.get("date", "Unknown"),
            "guest": metadata.get("guest", "Unknown"),
            "youtube_url": metadata.get("youtube_url", ""),
            "video_id": metadata.get("video_id", ""),
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", [])
        },
        "recommendations": {
            "books": [],
            "media": [],
            "products": []
        },
        "_lightning_round_text": lightning_section[:1000]  # Store sample for reference
    }

    # Save raw JSON
    slug = filepath.stem
    json_path = JSON_DIR / f"{slug}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(episode_data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved JSON: {json_path.name}")

    return episode_data

def generate_csv_row(episode_data, category, item):
    """Generate a CSV row from recommendation data."""
    metadata = episode_data["metadata"]

    if category == "Book":
        return {
            "Episode": metadata["title"],
            "Guest": metadata["guest"],
            "Date": metadata["date"],
            "Category": category,
            "Title": item.get("title", ""),
            "Author": item.get("author", ""),
            "Description": item.get("context", ""),
            "Amazon_URL": item.get("amazon_url", ""),
            "Image_URL": item.get("image_url", "")
        }
    elif category == "TV Show" or category == "Movie":
        return {
            "Episode": metadata["title"],
            "Guest": metadata["guest"],
            "Date": metadata["date"],
            "Category": category,
            "Title": item.get("title", ""),
            "Author": "N/A",
            "Description": item.get("context", ""),
            "Amazon_URL": "N/A",
            "Image_URL": "N/A"
        }
    elif category == "Product":
        return {
            "Episode": metadata["title"],
            "Guest": metadata["guest"],
            "Date": metadata["date"],
            "Category": category,
            "Title": item.get("name", ""),
            "Author": "N/A",
            "Description": item.get("context", ""),
            "Amazon_URL": item.get("url", "N/A"),
            "Image_URL": "N/A"
        }

def main():
    print("=" * 60)
    print("Lenny's Podcast Recommendations Extractor")
    print("=" * 60)
    print()

    # Get all podcast files
    podcast_files = sorted(PODCASTS_DIR.glob("*.md"))
    total_files = len(podcast_files)

    print(f"Found {total_files} podcast episodes to process")
    print()

    # Process each episode
    all_recommendations = []
    processed = 0
    skipped = 0

    for filepath in podcast_files:
        try:
            episode_data = process_episode(filepath)
            if episode_data:
                processed += 1

                # Collect recommendations for master CSV
                for book in episode_data["recommendations"]["books"]:
                    row = generate_csv_row(episode_data, "Book", book)
                    if row:
                        all_recommendations.append(row)

                for show in episode_data["recommendations"]["media"]:
                    category = "TV Show" if show.get("type") == "tv_show" else "Movie"
                    row = generate_csv_row(episode_data, category, show)
                    if row:
                        all_recommendations.append(row)

                for product in episode_data["recommendations"]["products"]:
                    row = generate_csv_row(episode_data, "Product", product)
                    if row:
                        all_recommendations.append(row)
            else:
                skipped += 1

        except Exception as e:
            print(f"  ✗ Error processing {filepath.name}: {e}")
            skipped += 1

        # Progress update every 10 files
        if (processed + skipped) % 10 == 0:
            print(f"\nProgress: {processed + skipped}/{total_files} files processed...")
            print()

    print()
    print("=" * 60)
    print(f"✓ Processed: {processed} episodes")
    print(f"⚠ Skipped: {skipped} episodes")
    print(f"📊 Total recommendations extracted: {len(all_recommendations)}")
    print()

    # Generate master CSV
    if all_recommendations:
        master_csv_path = OUTPUT_DIR / "all-recommendations.csv"

        fieldnames = ["Episode", "Guest", "Date", "Category", "Title", "Author",
                     "Description", "Amazon_URL", "Image_URL"]

        with open(master_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_recommendations)

        print(f"✓ Master CSV saved: {master_csv_path}")
    else:
        print("⚠️  No recommendations found - CSV not generated")

    print()
    print("=" * 60)
    print("NEXT STEP:")
    print("The script has created JSON files with episode metadata.")
    print("You'll need Claude to extract actual recommendations from the transcripts.")
    print("Run this script again after Claude processes the files.")
    print("=" * 60)

if __name__ == "__main__":
    main()
