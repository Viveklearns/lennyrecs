# Lenny's Podcast Recommendations Extraction Spec

## Overview
Extract all recommendations made by podcast guests across Lenny's podcast archive, along with episode metadata.

## Data to Extract

### 1. Episode Metadata
From the frontmatter of each markdown file:
- `title` - Full episode title
- `date` - Publication date
- `guest` - Guest name
- `youtube_url` - YouTube URL
- `video_id` - YouTube video ID
- `description` - Episode description
- `tags` - Episode tags/topics

### 2. Recommendations Categories

#### Books
- Book title
- Author (if mentioned)
- Context of recommendation (why it was recommended, if stated)
- Amazon URL (enriched after extraction)
- Book cover image URL (enriched after extraction)

#### Movies/TV Shows
- Title
- Type (movie or TV show)
- Context of recommendation

#### Products/Tools
- Product name
- Category (e.g., software, physical product, service)
- Context of recommendation

## Output Format

### Per Episode
```json
{
  "metadata": {
    "title": "string",
    "date": "string",
    "guest": "string",
    "youtube_url": "string",
    "video_id": "string",
    "description": "string",
    "tags": ["array"]
  },
  "recommendations": {
    "books": [
      {
        "title": "string",
        "author": "string (optional)",
        "context": "string (optional)",
        "amazon_url": "string (enriched)",
        "image_url": "string (enriched)"
      }
    ],
    "media": [
      {
        "title": "string",
        "type": "movie | tv_show",
        "context": "string (optional)"
      }
    ],
    "products": [
      {
        "name": "string",
        "category": "string (optional)",
        "context": "string (optional)"
      }
    ]
  }
}
```

### Aggregated Output
All episodes combined into a single data structure for easy querying and analysis.

## Extraction Method

**LLM-Based Extraction using Claude API:**
- Python script (`extract_all_with_api.py`) processes all 295 episodes
- Uses Claude 3.5 Sonnet via Anthropic API for intelligent extraction
- Focuses on "lightning round" section of each episode (last ~3000 chars if not found)
- Understands context: "I love X" or "You should check out Y" are identified as recommendations
- Extracts both guest AND host (Lenny) recommendations
- Cost: ~$3-5 for all episodes

## Enrichment Process

After initial extraction, book recommendations are enriched with additional data:

1. **Amazon URL Construction**:
   - For books: `https://amazon.com/s?k={title}+{author}`
   - This creates a search URL (not direct product link)
   - Users can find the book in search results

2. **Book Cover Images** (Optional - not implemented in v1):
   - Can use Open Library API: `https://openlibrary.org/search.json?title={title}&author={author}`
   - Extract ISBN from response
   - Get cover: `https://covers.openlibrary.org/b/isbn/{ISBN}-L.jpg`

Amazon URLs are added during extraction; book cover images are left as N/A in v1.

## Notes
- Recommendations typically appear in the "lightning round" section near the end of episodes
- Some episodes may have no recommendations
- Extract exact quotes when possible for context
- Maintain source traceability (which episode each recommendation came from)
