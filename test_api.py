#!/usr/bin/env python3
"""Test API calls to debug image fetching."""

import requests
import json

# Test Open Library
title = "Persuasion"
author = "Robert Cialdini"

print(f"Testing: {title} by {author}")
print()

# Open Library Search
print("Open Library Search:")
url = f"https://openlibrary.org/search.json?title={title}&author={author}"
print(f"URL: {url}")

response = requests.get(url)
data = response.json()

print(f"Found {data.get('numFound', 0)} results")
if "docs" in data and len(data["docs"]) > 0:
    doc = data["docs"][0]
    print(f"Title: {doc.get('title')}")
    print(f"Author: {doc.get('author_name')}")
    print(f"ISBNs: {doc.get('isbn', [])[:3]}")

    if "isbn" in doc and len(doc["isbn"]) > 0:
        isbn = doc["isbn"][0]
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        print(f"Cover URL: {cover_url}")

        # Test if cover exists
        head = requests.head(cover_url)
        print(f"Cover exists: {head.status_code == 200}")
