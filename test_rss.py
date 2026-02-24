import feedparser
import json
from datetime import datetime
import time

# pytrends is optional — script still works without it using RSS only
try:
    from pytrends.request import TrendReq
    PYTRENDS_AVAILABLE = True
except ImportError:
    PYTRENDS_AVAILABLE = False

feedparser.USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

style_keywords = [
    # Core aesthetics
    "streetwear",
    "y2k",
    "dark academia",
    "cottage core",
    "cottagecore",
    "clean girl",
    "gorpcore",
    "minimalist",
    "grunge",
    "preppy",
    "athleisure",
    "quiet luxury",
    "old money",
    "boho",
    "bohemian",
    "maximalist",
    "coastal grandmother",
    "barbiecore",
    "balletcore",
    "dopamine dressing",

    # Trending styles
    "mob wife",
    "tomato girl",
    "vanilla girl",
    "latte makeup",
    "office siren",
    "coquette",
    "blokecore",
    "indie sleaze",
    "regencycore",
    "downtown girl",
    "uptown girl",
    "model off duty",
    "brooklyn style",

    # Classic styles
    "casual chic",
    "business casual",
    "smart casual",
    "monochrome",
    "all black",
    "athflow",
    "normcore",
    "avant garde",
    "scandinavian style",
    "french girl",
    "parisian chic",

    # Specific trends
    "oversized",
    "baggy",
    "wide leg",
    "crop top",
    "cargo pants",
    "low rise",
    "high rise",
    "platform shoes",
    "chunky sneakers",
    "ballet flats",
    "mary janes",
    "kitten heels",

    # Fashion movements
    "sustainable fashion",
    "slow fashion",
    "vintage",
    "thrifted",
    "upcycled",
    "gender neutral",
    "androgynous",

    # Color trends
    "dopamine colors",
    "earth tones",
    "neutrals",
    "pastels",
    "neon",
    "all white",

    # Seasonal
    "spring fashion",
    "summer style",
    "fall fashion",
    "winter style",

    # Fabric/texture trends
    "leather",
    "denim",
    "linen",
    "silk",
    "velvet",
    "corduroy",
    "mesh",
    "sheer",

    # Pattern trends
    "animal print",
    "leopard print",
    "zebra print",
    "floral",
    "plaid",
    "checkered",
    "gingham",
    "stripes",
    "polka dot",
]

# All RSS feeds to scan
rss_feeds = [
    # Fashion Blogs & Magazines
    {"name": "Who What Wear", "url": "https://www.whowhatwear.com/rss"},
    {"name": "Fashionista", "url": "https://fashionista.com/feed"},
    {"name": "Vogue", "url": "https://www.vogue.com/feed/rss"},
    {"name": "Teen Vogue", "url": "https://www.teenvogue.com/feed/rss"},
    {"name": "Harper's Bazaar", "url": "https://www.harpersbazaar.com/rss/all.xml/"},
    {"name": "Elle", "url": "https://www.elle.com/rss/all.xml/"},
    {"name": "InStyle", "url": "https://www.instyle.com/rss/all.xml"},
    {"name": "Glamour", "url": "https://www.glamour.com/rss/all.xml"},
    {"name": "Marie Claire", "url": "https://www.marieclaire.com/rss/all.xml/"},
    {"name": "Cosmopolitan", "url": "https://www.cosmopolitan.com/rss/all.xml/"},
    {"name": "Refinery29", "url": "https://www.refinery29.com/en-us/rss.xml"},
    {"name": "The Cut", "url": "https://www.thecut.com/rss/index.xml"},
    {"name": "W Magazine", "url": "https://www.wmagazine.com/rss"},
    {"name": "Nylon", "url": "https://www.nylon.com/rss"},
    {"name": "WWD", "url": "https://wwd.com/feed/"},
    {"name": "Business of Fashion", "url": "https://www.businessoffashion.com/rss/"},
    # Streetwear & Hype Sites
    {"name": "Hypebeast", "url": "https://hypebeast.com/feed"},
    {"name": "Hypebae", "url": "https://hypebae.com/feed"},
    {"name": "Highsnobiety", "url": "https://www.highsnobiety.com/feed/"},
    {"name": "Complex Style", "url": "https://www.complex.com/rss"},
    # Google News Searches
    {"name": "Google News - Fashion Trends", "url": "https://news.google.com/rss/search?q=fashion+trends&hl=en-US"},
    {"name": "Google News - Street Style", "url": "https://news.google.com/rss/search?q=street+style+fashion&hl=en-US"},
    {"name": "Google News - Outfit Ideas", "url": "https://news.google.com/rss/search?q=outfit+ideas&hl=en-US"},
    {"name": "Google News - Style Trends 2026", "url": "https://news.google.com/rss/search?q=style+trends+2026&hl=en-US"},
    {"name": "Google News - Streetwear", "url": "https://news.google.com/rss/search?q=streetwear+trends&hl=en-US"},
    {"name": "Google News - Aesthetic Fashion", "url": "https://news.google.com/rss/search?q=aesthetic+fashion&hl=en-US"},
]

# ─────────────────────────────────────────────
# STEP 1: RSS FEED SCANNING
# ─────────────────────────────────────────────

style_counts = {style: 0 for style in style_keywords}
total_articles = 0
successful_feeds = 0

print("=" * 70)
print("FASHION TREND PARSER — RSS + GOOGLE TRENDS")
print("=" * 70)
print("\n📰 STEP 1: Parsing RSS feeds...\n")

for feed_info in rss_feeds:
    print(f"  Parsing {feed_info['name']}...")
    try:
        feed = feedparser.parse(feed_info['url'])

        if not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print(f"   ✗ No articles found")
            continue

        print(f"   ✓ {len(feed.entries)} articles")
        total_articles += len(feed.entries)
        successful_feeds += 1

        articles_with_matches = 0
        for entry in feed.entries:
            title = entry.title.lower() if hasattr(entry, 'title') else ""
            description = ""
            if hasattr(entry, 'summary'):
                description = entry.summary.lower()
            elif hasattr(entry, 'description'):
                description = entry.description.lower()

            full_text = title + " " + description
            found_in_article = False

            for style in style_keywords:
                if style in full_text:
                    style_counts[style] += 1
                    if not found_in_article:
                        articles_with_matches += 1
                        found_in_article = True

        print(f"   → {articles_with_matches} articles matched style keywords")
        time.sleep(0.5)

    except Exception as e:
        print(f"   ✗ Error: {str(e)[:60]}")

# Normalize RSS scores to 0–100
max_rss = max(style_counts.values()) if max(style_counts.values()) > 0 else 1
rss_normalized = {style: round((count / max_rss) * 100) for style, count in style_counts.items()}

# ─────────────────────────────────────────────
# STEP 2: GOOGLE TRENDS SCANNING
# ─────────────────────────────────────────────

trends_scores = {style: 0 for style in style_keywords}

print("\n" + "=" * 70)
print("📈 STEP 2: Fetching Google Trends data...")
print("=" * 70)

if not PYTRENDS_AVAILABLE:
    print("\n  ⚠️  pytrends not installed. Run: pip install pytrends")
    print("  Skipping Google Trends — using RSS data only.\n")
else:
    try:
        pytrends = TrendReq(hl='en-US', tz=300, timeout=(10, 25))

        # pytrends max 5 keywords per request — batch them up
        BATCH_SIZE = 5
        batches = [style_keywords[i:i+BATCH_SIZE] for i in range(0, len(style_keywords), BATCH_SIZE)]
        successful_batches = 0

        print(f"\n  Querying {len(batches)} batches of up to {BATCH_SIZE} keywords (past 7 days)...\n")

        for i, batch in enumerate(batches):
            try:
                pytrends.build_payload(batch, cat=0, timeframe='now 7-d', geo='US', gprop='')
                interest_df = pytrends.interest_over_time()

                if interest_df.empty:
                    print(f"  Batch {i+1}/{len(batches)}: no data returned")
                    time.sleep(1)
                    continue

                # Average interest across the time window for each keyword
                for keyword in batch:
                    if keyword in interest_df.columns:
                        avg_score = int(interest_df[keyword].mean())
                        trends_scores[keyword] = avg_score

                hits = [k for k in batch if trends_scores[k] > 0]
                print(f"  Batch {i+1}/{len(batches)}: ✓ got data for {len(hits)}/{len(batch)} keywords")
                successful_batches += 1

                # Be polite — Google will rate-limit if you hammer it
                time.sleep(2)

            except Exception as e:
                print(f"  Batch {i+1}/{len(batches)}: ✗ {str(e)[:60]}")
                time.sleep(3)

        print(f"\n  ✓ Google Trends: {successful_batches}/{len(batches)} batches succeeded")

    except Exception as e:
        print(f"\n  ✗ Google Trends failed entirely: {str(e)[:80]}")
        print("  Falling back to RSS-only scoring.\n")

# ─────────────────────────────────────────────
# STEP 3: COMBINE SCORES
# ─────────────────────────────────────────────
# Weights: 60% RSS (editorial coverage) + 40% Google Trends (search interest)
# If Trends data is all zeros (failed), fall back to 100% RSS

trends_total = sum(trends_scores.values())
RSS_WEIGHT = 0.6 if trends_total > 0 else 1.0
TRENDS_WEIGHT = 0.4 if trends_total > 0 else 0.0

combined_scores = {}
for style in style_keywords:
    combined_scores[style] = round(
        (rss_normalized[style] * RSS_WEIGHT) +
        (trends_scores[style] * TRENDS_WEIGHT)
    )

sorted_styles = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

# ─────────────────────────────────────────────
# STEP 4: PRINT RESULTS
# ─────────────────────────────────────────────

print("\n" + "=" * 70)
print("📊 FINAL RESULTS  (RSS {:.0f}% + Google Trends {:.0f}%)".format(RSS_WEIGHT*100, TRENDS_WEIGHT*100))
print("=" * 70)
print(f"  RSS  → {successful_feeds}/{len(rss_feeds)} feeds, {total_articles} articles")
if PYTRENDS_AVAILABLE and trends_total > 0:
    print(f"  Trends → {sum(1 for v in trends_scores.values() if v > 0)} keywords with search data")
print()

print("🔥 TRENDING STYLES:")
print("-" * 70)
rank = 1
for style, score in sorted_styles:
    if score > 0:
        rss_part  = rss_normalized[style]
        trend_part = trends_scores[style]
        emoji = "🔥" if rank <= 3 else "📈"
        print(f"  {emoji} #{rank:2d}  {style.title():<25} score={score:3d}  (rss={rss_part}, trends={trend_part})")
        rank += 1
        if rank > 20:
            break

# ─────────────────────────────────────────────
# STEP 5: SAVE OUTPUT
# ─────────────────────────────────────────────

results = {
    "source": "rss_and_google_trends",
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_articles_analyzed": total_articles,
    "successful_feeds": successful_feeds,
    "total_feeds_attempted": len(rss_feeds),
    "google_trends_available": PYTRENDS_AVAILABLE and trends_total > 0,
    "weights": {"rss": RSS_WEIGHT, "google_trends": TRENDS_WEIGHT},
    "trending_styles": [
        {
            "style": style,
            "score": score,
            "rss_score": rss_normalized[style],
            "trends_score": trends_scores[style],
            "rank": i + 1
        }
        for i, (style, score) in enumerate(sorted_styles) if score > 0
    ]
}

output_file = 'trending_styles.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

js_file = 'trending_styles_data.js'
with open(js_file, 'w') as f:
    f.write('window.TRENDING_STYLES = ' + json.dumps(results) + ';\n')

print("\n" + "=" * 70)
print(f"💾 Saved to '{output_file}' and '{js_file}'")
print("=" * 70)
