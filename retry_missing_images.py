#!/usr/bin/env python3
"""
Retry fetching images for the 50 books that got placeholder images.
Uses improved search strategies.
"""

import os
import requests
import time
from pathlib import Path
from difflib import SequenceMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
BASE_DIR = Path("/Users/vivekgupta/Downloads/lennyrecs")
IMAGES_DIR = BASE_DIR / "images" / "books"
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
GOOGLE_BOOKS_API = "https://www.googleapis.com/books/v1/volumes"

# Placeholder checksum to identify
PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

# Books that have placeholder images
PLACEHOLDER_BOOKS = [
    ("15 Commitments of Conscious Leadership", "Jim Dethmer and Diana Chapman"),
    ("7 Powers", "Hamilton Helmer"),
    ("A Deepness in the Sky", "N/A"),
    ("Accelerate", "N/A"),
    ("Breakneck", "Dan Wang"),
    ("Carry On, Jeeves", "P.G. Wodehouse"),
    ("Competing Against Luck", "Clayton Christensen"),
    ("Dare to Lead Like a Girl", "Dalia Feldheim"),
    ("End of Average", "Todd Rose"),
    ("Founding Sales", "Pete Kazanjy"),
    ("From Third World to First", "Lee Kuan Yew"),
    ("Getting Real", "37 Signals"),
    ("Good to Great", "N/A"),
    ("How Brands Grow", "Byron Sharp"),
    ("How to Get Rich", "Felix Dennis"),
    ("It's Not How Good You Are, It's How Good You Want to Be", "Paul Arden"),
    ("Kindred", "Octavia Butler"),
    ("Le Ton beau de Marot", "Douglas Hofstadter"),
    ("Metabolical", "N/A"),
    ("Mistakes Were Made (But Not by Me)", "N/A"),
    ("Obviously Awesome", "April Dunford"),
    ("Orbiting the Giant Hairball: A Corporate Fool's Guide to Surviving with Grace", "Gordon MacKenzie"),
    ("Out of Sheer Rage", "Geoff Dyer"),
    ("Pachinko", "Min Jin Lee"),
    ("Power: Why Some People Have It and Others Don't", "Jeffrey Pfeffer"),
    ("Radical Focus", "Christina Wodtke"),
    ("Range", "David Epstein"),
    ("Replacing Guilt", "Nate Soares"),
    ("Revolt of the Public", "N/A"),
    ("Roald Dahl books (including Witches and Matilda)", "Roald Dahl"),
    ("Simple Path to Wealth", "JL Collins"),
    ("Snuggle Puppy", "N/A"),
    ("Strong Product People", "Petra Wille"),
    ("The Boy, the Mole, the Fox, and the Horse", "N/A"),
    ("The Case Against Reality", "Donald Hoffman"),
    ("The Elements of Thinking in Systems", "N/A"),
    ("The Fabric of Reality", "David Deutch"),
    ("The Myth of Sisyphus", "Albert Camus"),
    ("The Person and the Situation", "N/A"),
    ("The Road to Reality", "Roger Penrose"),
    ("The Wandering Earth", "Liu Cixin"),
    ("The Writer's Journey", "Chris Vogler"),
    ("Treasure Island", "N/A"),
    ("Tress by the Emerald Sea", "Brandon Sanderson"),
    ("Why We Sleep", "N/A"),
    ("Winston Churchill biography", "Andrew Roberts"),
]

def similar(a, b):
    """Check if two strings are similar (for title matching)."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def search_google_books(title, author, strategy="default"):
    """Search Google Books with different strategies. Returns list of (url, score, book_id) tuples."""

    # Strategy 1: intitle: and inauthor:
    if strategy == "exact":
        if author and author != "N/A":
            query = f'intitle:"{title}" inauthor:"{author}"'
        else:
            query = f'intitle:"{title}"'

    # Strategy 2: Just title in quotes
    elif strategy == "title_only":
        query = f'intitle:"{title}"'

    # Strategy 3: Title without quotes + author
    elif strategy == "loose":
        query = f"{title}"
        if author and author != "N/A":
            query += f" {author}"

    # Default
    else:
        query = f"{title}"
        if author and author != "N/A":
            query += f" {author}"

    try:
        params = {
            "q": query,
            "key": GOOGLE_BOOKS_API_KEY,
            "maxResults": 5  # Get top 5 to find best match
        }

        response = requests.get(GOOGLE_BOOKS_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if "items" in data:
            # Collect ALL results with imageLinks, sorted by score
            results = []

            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                result_title = volume_info.get("title", "")
                result_authors = volume_info.get("authors", [])
                image_links = volume_info.get("imageLinks", {})
                book_id = item.get("id", "")

                # Skip if no image
                if not image_links:
                    continue

                # Score this result
                title_score = similar(title, result_title)

                # If we have an author, check author match too
                if author and author != "N/A" and result_authors:
                    author_str = " ".join(result_authors)
                    author_score = similar(author, author_str)
                    total_score = (title_score * 0.7) + (author_score * 0.3)
                else:
                    total_score = title_score

                # Only consider decent matches
                if total_score > 0.6:
                    # Get best quality image URL
                    image_url = None
                    if "large" in image_links:
                        image_url = image_links["large"]
                    elif "medium" in image_links:
                        image_url = image_links["medium"]
                    elif "thumbnail" in image_links:
                        thumb = image_links["thumbnail"]
                        thumb = thumb.replace("http://", "https://")
                        thumb = thumb.replace("zoom=1", "zoom=2")
                        image_url = thumb

                    if image_url:
                        results.append((image_url, total_score, book_id))

            # Sort by score (highest first)
            results.sort(key=lambda x: x[1], reverse=True)
            return results

        return []

    except Exception as e:
        print(f"    Error: {e}")
        return []

def download_image(url, filepath):
    """Download image from URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(response.content)

        return True
    except Exception as e:
        print(f"    Download error: {e}")
        return False

def main():
    print("=" * 70)
    print("Retrying 50 Books with Placeholder Images")
    print("=" * 70)
    print()

    success_count = 0
    strategies = ["exact", "title_only", "loose"]  # Only top 3 strategies

    PLACEHOLDER_MD5 = "c96309220b9cbd205c36d879d09a3647"

    for i, (title, author) in enumerate(PLACEHOLDER_BOOKS, 1):
        print(f"[{i}/{len(PLACEHOLDER_BOOKS)}] {title}")
        print(f"    Author: {author}")

        # Collect all possible image URLs from all strategies
        all_results = []

        # Try strategies with delays between each
        for strategy in strategies:
            results = search_google_books(title, author, strategy)
            if results:
                for url, score, book_id in results:
                    all_results.append((url, score, strategy, book_id))

            # Wait 1 second between strategies to avoid rate limiting
            time.sleep(1)

        if all_results:
            # Sort by score (highest first)
            all_results.sort(key=lambda x: x[1], reverse=True)

            # Try each result until we find a non-placeholder
            downloaded = False
            author_normalized = author.replace('/', '-')
            filename = f"{title}_{author_normalized}.jpg"
            filepath = IMAGES_DIR / filename

            for url, score, strategy, book_id in all_results:
                print(f"    Trying: score={score:.2f}, strategy={strategy}, book_id={book_id[:12]}...")

                if download_image(url, filepath):
                    # Check if it's a placeholder
                    import hashlib
                    with open(filepath, 'rb') as f:
                        file_md5 = hashlib.md5(f.read()).hexdigest()

                    file_size = filepath.stat().st_size

                    if file_md5 == PLACEHOLDER_MD5 or file_size < 10000:
                        print(f"      ✗ Placeholder detected ({file_size} bytes), trying next...")
                        continue
                    else:
                        print(f"      ✓ Real cover found! ({file_size} bytes)")
                        downloaded = True
                        success_count += 1
                        break
                else:
                    print(f"      ✗ Download failed, trying next...")

            if not downloaded:
                print(f"    ✗ All options exhausted - no real cover found")
        else:
            print(f"    ✗ No match found")

        print()

        # Wait 2 seconds between books to avoid rate limiting
        time.sleep(2)

    print("=" * 70)
    print(f"✅ Complete: {success_count}/{len(PLACEHOLDER_BOOKS)} covers downloaded")
    print(f"Success rate: {success_count*100//len(PLACEHOLDER_BOOKS)}%")
    print("=" * 70)

if __name__ == "__main__":
    main()
