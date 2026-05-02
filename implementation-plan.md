# Implementation Plan - Lenny's Podcast Recommendations Extraction

## Overview
This document describes the chosen implementation approach for extracting and enriching recommendations from all podcast episodes.

## Pipeline Steps

### Step 1: Automated Extraction (Claude API)
**Tool:** Python script with Claude 3.5 Sonnet API
**Script:** `extract_all_with_api.py`
**Input:** All 295 markdown transcript files

**Process:**
1. For each episode:
   - Read markdown file
   - Extract metadata from frontmatter
   - Extract lightning round section (or last 3000 chars)
   - Send to Claude API with extraction prompt
   - Parse JSON response
   - Append directly to master CSV

2. Claude API extracts:
   - Books (title, author, context)
   - TV shows/movies (title, type, context)
   - Products/Podcasts/Newsletters (name, category, context)

3. Amazon URLs constructed automatically:
   - Books: `https://amazon.com/s?k={title}+{author}`
   - Products: From context if mentioned, else N/A

**Output:** Appends to `extracted/all-recommendations.csv`

**Features:**
- Progress tracking (saves which episodes processed)
- Resumable (can restart if interrupted)
- Rate limiting (1 second between requests)
- Error handling (logs failed episodes)

**Cost:** ~$3-5 for all 295 episodes

---

### Step 2: CSV Output (Automated)
**Format:** Master CSV file with columns:
- Episode - Episode title
- Guest - Guest name
- Date - Episode date
- Category - Book | TV Show | Movie | Product | Podcast | Newsletter
- Title - Name of recommendation
- Author - Author/creator (N/A for products)
- Description - Context about why recommended
- Amazon_URL - Amazon search URL (for books)
- Image_URL - N/A (future enhancement)

**Output:** `extracted/all-recommendations.csv`

---

### Step 3: Future Enhancements (Not in v1)
**Book Cover Images:**
- Can use Open Library API after extraction
- Query: `https://openlibrary.org/search.json?title={title}&author={author}`
- Extract ISBN, fetch cover from `https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg`

**Direct Amazon Links:**
- Would require ISBN lookup
- Current approach uses search URLs which work but aren't direct product links

---

## File Structure

```
lennyrecs/
├── spec.md                           # What we're extracting
├── extraction-prompt.md              # LLM prompt for extraction
├── technical-approaches.md           # Analysis of different approaches
├── implementation-plan.md            # This file - chosen approach
├── validation-and-enrichment-approaches.md  # Detailed approach analysis
│
├── 03-podcasts/                      # Original transcripts
│   ├── ada-chen-rekhi.md
│   ├── adam-fishman.md
│   └── ...
│
├── extracted/                        # Generated data (create this)
│   ├── json/                         # Raw + enriched JSON
│   │   ├── ada-chen-rekhi-raw.json
│   │   ├── ada-chen-rekhi-enriched.json
│   │   └── ...
│   │
│   ├── csv/                          # Individual episode CSVs
│   │   ├── ada-chen-rekhi.csv
│   │   └── ...
│   │
│   └── all-recommendations.csv       # Master file
```

---

## Tools & APIs

### Required
- **Claude (LLM):** For extraction and ISBN lookup via knowledge
- **Open Library API:** For book validation and cover images
  - Endpoint: `https://openlibrary.org/search.json`
  - Rate limit: None (unlimited)
  - Auth: None required

### Optional
- **Google Books API:** Backup if Open Library fails
  - Rate limit: 1000 requests/day
  - Would need API key for higher limits

---

## Execution Plan

### For Single Episode Test
1. Extract: Ada Chen Rekhi episode → raw JSON
2. Enrich: Add ISBNs, Amazon URLs, cover images → enriched JSON
3. Convert: Generate CSV
4. Review: Validate output quality

### For All 295 Episodes
1. **Batch extraction:** Process all episodes sequentially
   - Read transcript
   - Extract recommendations
   - Save raw JSON
   - Estimated time: 30-60 minutes

2. **Batch enrichment:** Enrich all books
   - Query Open Library API (with 1 second delay between requests)
   - Add ISBNs and cover images
   - Estimated time: 20-30 minutes

3. **Generate CSVs:** Convert all JSON to CSV
   - Estimated time: 5 minutes

4. **Aggregate:** Combine into master CSV
   - Estimated time: 1 minute

**Total estimated time: 1-2 hours**

---

## Error Handling

### Book not found in Open Library
- Fall back to Amazon search URL
- Set image_url to null
- Flag for manual review

### Missing author
- Search by title only
- Include in results with "Author unknown"

### API rate limits
- Add 1 second delay between requests
- Retry failed requests once
- Continue processing, flag failures

### Malformed data
- Log error
- Skip that recommendation
- Continue processing rest of episode

---

## Quality Assurance

1. **Spot check:** Manually review 10 random episodes
2. **Validation metrics:**
   - % of books with direct Amazon URLs (target: >80%)
   - % of books with cover images (target: >85%)
   - % of episodes with at least 1 recommendation (expected: ~95%)
3. **Manual review queue:** Flag items for review if:
   - Book title is very short (<5 chars)
   - No author found
   - Open Library returns 0 results

---

## Next Steps

1. ✅ Spec defined
2. ✅ Extraction prompt created
3. ✅ Enrichment approach decided
4. ⏳ Test end-to-end on 1 episode
5. ⏳ Run on all 295 episodes
6. ⏳ Generate master CSV
7. ⏳ Manual QA review
