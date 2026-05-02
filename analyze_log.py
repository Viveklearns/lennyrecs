#!/usr/bin/env python3
"""Analyze the book image retrieval log."""

import csv
from collections import defaultdict

LOG_FILE = "/Users/vivekgupta/Downloads/lennyrecs/book_image_retrieval_log.csv"

# Read log
with open(LOG_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Analysis
books_attempted = set()
books_succeeded = set()
strategy_success = defaultdict(int)
strategy_attempts = defaultdict(int)
book_attempts = defaultdict(list)

for row in rows:
    book = row['book_title']
    books_attempted.add(book)

    strategy = row['strategy_name']
    final_success = row['final_success'] == 'True'

    if strategy != 'all_strategies':
        strategy_attempts[strategy] += 1
        if final_success:
            strategy_success[strategy] += 1

    if final_success:
        books_succeeded.add(book)
        book_attempts[book].append({
            'strategy': strategy,
            'book_id': row['book_id'],
            'api_url': row['api_url'][:80] + '...',
            'file_size': row['file_size_bytes'],
            'score': row['match_score']
        })

print("=" * 80)
print("BOOK IMAGE RETRIEVAL ANALYSIS")
print("=" * 80)
print()
print(f"📊 OVERALL STATS:")
print(f"   Books attempted: {len(books_attempted)}")
print(f"   Books succeeded: {len(books_succeeded)}")
print(f"   Books still missing: {len(books_attempted) - len(books_succeeded)}")
print(f"   Success rate: {len(books_succeeded) * 100 // len(books_attempted)}%")
print()

print(f"📈 STRATEGY PERFORMANCE:")
for strategy in ['exact', 'title_only', 'loose']:
    attempts = strategy_attempts[strategy]
    successes = strategy_success[strategy]
    rate = (successes * 100 // attempts) if attempts > 0 else 0
    print(f"   {strategy:12s}: {successes:2d}/{attempts:2d} = {rate}%")
print()

print(f"✅ SUCCESSFUL DOWNLOADS ({len(books_succeeded)} books):")
for i, book in enumerate(sorted(books_succeeded), 1):
    attempts = book_attempts[book]
    if attempts:
        first = attempts[0]
        print(f"   {i:2d}. {book}")
        print(f"       Strategy: {first['strategy']}, Score: {first['score']}, Size: {first['file_size']} bytes")
        print(f"       Book ID: {first['book_id']}")
print()

print(f"❌ STILL MISSING ({len(books_attempted) - len(books_succeeded)} books):")
missing = sorted(books_attempted - books_succeeded)
for i, book in enumerate(missing, 1):
    print(f"   {i:2d}. {book}")
print()

print("=" * 80)
print(f"📋 Full log available at: {LOG_FILE}")
print("=" * 80)
