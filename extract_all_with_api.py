#!/usr/bin/env python3
"""
Extract all recommendations from Lenny's Podcast transcripts using Claude API.
"""

import os
import json
import csv
import re
import time
from pathlib import Path
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
API_KEY = os.getenv("ANTHROPIC_API_KEY")
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
PODCASTS_DIR = BASE_DIR / "03-podcasts"
OUTPUT_CSV = BASE_DIR / "extracted" / "all-recommendations.csv"
PROGRESS_FILE = BASE_DIR / "extracted" / "progress.json"

# Initialize Anthropic client
client = Anthropic(api_key=API_KEY)

# Already processed episodes (skip these)
ALREADY_DONE = [
    "ada-chen-rekhi", "adam-fishman", "adriel-frederick", "alisa-cohn",
    "ami-vora", "andrew-wilkinson", "annie-pearl", "arielle-jackson",
    "asha-sharma", "bill-carr", "adam-grenier"
]

def extract_metadata(content):
    """Extract frontmatter metadata from markdown file."""
    metadata = {}
    frontmatter_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
    if not frontmatter_match:
        return metadata

    frontmatter = frontmatter_match.group(1)
    for line in frontmatter.split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip().strip('"')
            if value.startswith('[') and value.endswith(']'):
                value = [v.strip().strip('"') for v in value[1:-1].split(',')]
            metadata[key] = value

    return metadata

def extract_lightning_round(content):
    """Extract the lightning round section from transcript."""
    match = re.search(r'lightning round', content, re.IGNORECASE)
    if match:
        return content[match.start():]
    # Return last 3000 characters if no lightning round found
    return content[-3000:]

def extract_recommendations(transcript, title, guest, date):
    """Use Claude API to extract recommendations from transcript."""

    lightning_section = extract_lightning_round(transcript)

    prompt = f"""You are analyzing a podcast transcript to extract all recommendations made by the guest.

Episode: {title}
Guest: {guest}
Date: {date}

Extract ALL recommendations in these categories:
1. BOOKS - Include title, author (if mentioned), and context
2. TV SHOWS/MOVIES - Include title, type (tv_show or movie), and context
3. PODCASTS/NEWSLETTERS - Include title and context
4. PRODUCTS - Include name, category, and context

Guidelines:
- Extract what's actually in the transcript, don't make things up
- Context should be 1-2 sentences about why they recommend it
- If author/details aren't mentioned, use "N/A"
- Include both guest AND host (Lenny) recommendations
- Understand context - "I love X" or "You should check out Y" are recommendations

Here's the lightning round section:

{lightning_section[:8000]}

Return ONLY valid JSON in this exact format:
{{
  "books": [
    {{"title": "Book Title", "author": "Author Name", "context": "Why they recommend it"}}
  ],
  "media": [
    {{"title": "Show/Movie", "type": "tv_show", "context": "Why they like it"}}
  ],
  "products": [
    {{"name": "Product Name", "category": "Type", "context": "Why they use it"}}
  ]
}}

If no recommendations in a category, use empty array [].
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = response.content[0].text

        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
        else:
            print(f"  ⚠️  No JSON found in response")
            return {"books": [], "media": [], "products": []}

    except Exception as e:
        print(f"  ✗ API Error: {e}")
        return {"books": [], "media": [], "products": []}

def save_to_csv(episode_title, guest, date, recommendations, csv_file):
    """Append recommendations to CSV file."""

    rows = []

    # Books
    for book in recommendations.get("books", []):
        amazon_url = f"https://www.amazon.com/s?k={book['title'].replace(' ', '+')}+{book.get('author', '').replace(' ', '+')}"
        rows.append({
            "Episode": episode_title,
            "Guest": guest,
            "Date": date,
            "Category": "Book",
            "Title": book["title"],
            "Author": book.get("author", "N/A"),
            "Description": book.get("context", ""),
            "Amazon_URL": amazon_url if book.get("author") != "N/A" else "N/A",
            "Image_URL": "N/A"
        })

    # Media (TV/Movies)
    for item in recommendations.get("media", []):
        rows.append({
            "Episode": episode_title,
            "Guest": guest,
            "Date": date,
            "Category": "TV Show" if item.get("type") == "tv_show" else "Movie",
            "Title": item["title"],
            "Author": "N/A",
            "Description": item.get("context", ""),
            "Amazon_URL": "N/A",
            "Image_URL": "N/A"
        })

    # Products
    for product in recommendations.get("products", []):
        rows.append({
            "Episode": episode_title,
            "Guest": guest,
            "Date": date,
            "Category": "Product",
            "Title": product["name"],
            "Author": "N/A",
            "Description": product.get("context", ""),
            "Amazon_URL": product.get("url", "N/A"),
            "Image_URL": "N/A"
        })

    # Append to CSV
    if rows:
        file_exists = csv_file.exists()
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = ["Episode", "Guest", "Date", "Category", "Title", "Author",
                         "Description", "Amazon_URL", "Image_URL"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerows(rows)

    return len(rows)

def load_progress():
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {"processed": [], "failed": []}

def save_progress(progress):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def main():
    print("=" * 70)
    print("Lenny's Podcast Recommendations Extractor (Claude API)")
    print("=" * 70)
    print()

    # Get all podcast files
    podcast_files = sorted(PODCASTS_DIR.glob("*.md"))
    total_files = len(podcast_files)

    print(f"Found {total_files} podcast episodes")
    print(f"Already processed: {len(ALREADY_DONE)} episodes")
    print()

    # Load progress
    progress = load_progress()

    processed = 0
    skipped = 0
    failed = 0
    total_recs = 0

    for i, filepath in enumerate(podcast_files, 1):
        slug = filepath.stem

        # Skip if already done
        if slug in ALREADY_DONE or slug in progress["processed"]:
            skipped += 1
            continue

        print(f"[{i}/{total_files}] Processing: {slug}")

        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata
            metadata = extract_metadata(content)
            if not metadata:
                print(f"  ⚠️  No metadata, skipping...")
                progress["failed"].append(slug)
                failed += 1
                continue

            title = metadata.get("title", "Unknown")
            guest = metadata.get("guest", "Unknown")
            date = metadata.get("date", "Unknown")

            # Extract recommendations using Claude API
            print(f"  → Calling Claude API...")
            recommendations = extract_recommendations(content, title, guest, date)

            # Save to CSV
            num_recs = save_to_csv(title, guest, date, recommendations, OUTPUT_CSV)
            total_recs += num_recs

            print(f"  ✓ Extracted {num_recs} recommendations")

            # Mark as processed
            progress["processed"].append(slug)
            processed += 1

            # Save progress
            save_progress(progress)

            # Rate limiting - wait 1 second between requests
            time.sleep(1)

            # Progress update every 10 episodes
            if processed % 10 == 0:
                print()
                print(f"📊 Progress: {processed} processed, {total_recs} recommendations extracted")
                print()

        except Exception as e:
            print(f"  ✗ Error: {e}")
            progress["failed"].append(slug)
            failed += 1
            save_progress(progress)

    print()
    print("=" * 70)
    print("✅ COMPLETE!")
    print(f"Processed: {processed} episodes")
    print(f"Skipped: {skipped} episodes (already done)")
    print(f"Failed: {failed} episodes")
    print(f"Total recommendations: {total_recs}")
    print()
    print(f"Output saved to: {OUTPUT_CSV}")
    print("=" * 70)

if __name__ == "__main__":
    main()
