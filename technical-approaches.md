# Technical Approaches for Extracting Recommendations

## Approach 1: LLM-Based Extraction (Claude/GPT)

### Method
Use an LLM to read each markdown file and extract recommendations in a structured format.

**Implementation:**
- Read each markdown file
- Send the transcript to Claude/GPT with a structured prompt asking for recommendations
- Parse the LLM response (JSON) and store results

### Benefits
- **High accuracy**: LLMs understand context, can distinguish between a guest recommendation vs. just mentioning something
- **Handles ambiguity**: Can interpret "I loved X" or "You should check out Y" as recommendations
- **Extracts context naturally**: Can pull out why something was recommended
- **Flexible**: Can handle variations in how recommendations are stated
- **Low code complexity**: Minimal parsing logic needed

### Challenges
- **Cost**: ~294 files × ~15k-20k words each = significant API costs (though batch processing could reduce this)
- **Rate limits**: May need to throttle requests to stay within API limits
- **Consistency**: LLM outputs can vary slightly between runs
- **Token limits**: Very long transcripts might need chunking or focusing on "lightning round" sections only
- **Requires validation**: Should manually check a sample to ensure quality

### Estimated Time
- Development: 2-3 hours
- Processing: 2-4 hours (depending on rate limits)
- Total: ~1 day

---

## Approach 2: Hybrid - Pattern Matching + LLM Validation

### Method
First use regex/pattern matching to find the "lightning round" section, then use LLM only on that smaller section.

**Implementation:**
- Scan markdown for section markers like "lightning round", "favorite book", "favorite product"
- Extract just that section (much smaller text)
- Use LLM on the small section to extract structured data

### Benefits
- **Cost-effective**: Only sending ~500-1000 words per episode instead of 15k+
- **Faster processing**: Smaller token counts = faster responses
- **Focused extraction**: Lightning round is where 90%+ of recommendations appear
- **Still intelligent**: LLM handles the hard part of understanding recommendations
- **More reliable**: Section detection is deterministic, extraction is intelligent

### Challenges
- **Lightning round detection**: Not all episodes may use the same section markers
- **May miss recommendations**: Some recommendations appear in main conversation
- **Two-phase complexity**: Need both pattern matching AND LLM logic
- **Section boundary errors**: Might cut off mid-recommendation if section detection is wrong

### Estimated Time
- Development: 4-6 hours
- Processing: 30-60 minutes
- Total: ~1 day

---

## Approach 3: Pure Pattern Matching + Manual Review

### Method
Use regex patterns to find book titles, product names, and show titles based on common patterns.

**Implementation:**
- Search for patterns like: "book I recommend", "favorite movie", "product I love"
- Use regex to extract quoted titles, proper nouns after these patterns
- Export to CSV for manual review and cleanup

### Benefits
- **No API costs**: Completely free
- **Very fast**: Can process all 294 files in minutes
- **Deterministic**: Same results every time
- **Full control**: Exactly what patterns to look for

### Challenges
- **Low accuracy**: Will miss contextual recommendations ("I love Severance" without saying "show")
- **Many false positives**: Will capture things that aren't recommendations
- **Requires significant manual cleanup**: Human review needed for every result
- **Misses context**: Won't understand WHY something was recommended
- **Fragile**: Different phrasing breaks the patterns
- **Labor intensive**: Manual review of 294 episodes is time-consuming

### Estimated Time
- Development: 3-4 hours
- Processing: 5 minutes
- Manual review/cleanup: 10-20 hours
- Total: 2-3 days

---

## Recommendation Matrix

| Criteria | Approach 1 (Full LLM) | Approach 2 (Hybrid) | Approach 3 (Pattern Matching) |
|----------|---------------------|-------------------|---------------------------|
| **Accuracy** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Cost** | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Speed** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Automation** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Maintenance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## My Recommendation: Approach 2 (Hybrid)

**Why:**
1. **Best balance**: High accuracy at reasonable cost
2. **Lightning rounds are structured**: They follow a consistent Q&A format that's easy to detect
3. **90%+ coverage**: Most recommendations are in the lightning round section
4. **Cost-efficient**: ~500 words/episode vs 15,000 words = 30x cost reduction
5. **Fast iteration**: Can test on a few episodes quickly to validate approach

**Implementation Strategy:**
1. Build section detector (find "lightning round" variants)
2. Test on 10 episodes manually to validate detection accuracy
3. Build LLM extraction prompt with structured JSON output
4. Process all 294 episodes
5. Manual spot-check 20 random episodes for quality
6. If needed, run full-file LLM extraction on episodes where section detection failed

**Fallback:** For episodes where section detection fails or returns no results, fall back to Approach 1 (full file LLM extraction) for just those episodes.
