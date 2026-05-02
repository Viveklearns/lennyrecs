# Podcast Recommendation Extraction Prompt

Use this prompt when extracting recommendations from podcast transcript markdown files.

---

## Instructions

You are analyzing a podcast transcript to extract all recommendations made by the guest (and occasionally the host).

### What to Extract

#### 1. Episode Metadata
From the frontmatter (top of markdown file):
- title
- date
- guest
- youtube_url
- video_id
- description
- tags

#### 2. Book Recommendations
Extract ALL books mentioned as recommendations, whether in:
- The "lightning round" section
- Casual mentions during conversation
- References to books that influenced thinking

For each book, capture:
- **title**: Book title
- **author**: Author name (if mentioned; null if not)
- **context**: A concise 1-2 sentence description capturing:
  - Who recommended it (guest or host)
  - Why they recommend it / what it's useful for
  - Any notable context about the book

Format: "[Title] by [Author] — [Context]"

Example: "Persuasion by Robert Cialdini — Ada's top pick. A breakdown of strategies for getting people to say yes; useful for marketers, founders, and product people."

#### 3. Movies/TV Shows
Extract shows or movies recommended, capturing:
- **title**: Show/movie name
- **type**: "movie" or "tv_show"
- **context**: Why they like it, what they said about it

#### 4. Products/Tools
Extract any products, apps, or tools recommended:
- **name**: Product name
- **category**: Type of product (e.g., "productivity app", "browser", "SaaS tool")
- **context**: Why they use it, what problem it solves
- **url**: Website URL if mentioned (null if not)

### Important Guidelines

1. **Understand context, don't pattern match**: A recommendation can be phrased as:
   - "I recommend X"
   - "I love X"
   - "X has been really helpful"
   - "I use X all the time"
   - Simply answering "What's your favorite book?" with a title

2. **Include casual mentions**: If someone says "I read Radical Candor and it changed how I give feedback," that's a recommendation even if not in the lightning round.

3. **Distinguish guest vs. host**: Note in context if Lenny (the host) recommended something vs. the guest.

4. **No hallucination**: Only extract what's actually in the transcript. If author isn't mentioned, set to null. If context is minimal, keep it minimal.

5. **Amazon URL and image_url**: Set these to null during extraction. They will be enriched later.

### Output Format

Return a single JSON object with this structure:

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
        "author": "string or null",
        "context": "string",
        "amazon_url": null,
        "image_url": null
      }
    ],
    "media": [
      {
        "title": "string",
        "type": "movie or tv_show",
        "context": "string"
      }
    ],
    "products": [
      {
        "name": "string",
        "category": "string",
        "context": "string",
        "url": "string or null"
      }
    ]
  }
}
```

### Edge Cases

- If a book is mentioned but NOT as a recommendation (e.g., "I disagree with X"), don't include it
- If no recommendations exist in a category, use empty array: `[]`
- If the entire transcript has no recommendations, all arrays should be empty
- Products the guest created (like Ada's Notejoy) should still be included if they talk about using it
