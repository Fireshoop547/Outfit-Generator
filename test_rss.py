import feedparser
import json
from datetime import datetime
import time

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

# Initialize counter
style_counts = {}
for style in style_keywords:
    style_counts[style] = 0

total_articles = 0
successful_feeds = 0

# Parse all feeds
print("=" * 70)
print("FASHION TREND PARSER")
print("=" * 70)
print("\nParsing RSS feeds from working sources...\n")

for feed_info in rss_feeds:
    print(f"📰 Parsing {feed_info['name']}...")
    
    try:
        feed = feedparser.parse(feed_info['url'])
        
        if not hasattr(feed, 'entries') or len(feed.entries) == 0:
            print(f"   ✗ No articles found")
            continue
        
        print(f"   ✓ Found {len(feed.entries)} articles")
        total_articles += len(feed.entries)
        successful_feeds += 1
        
        # Loop through articles
        articles_with_matches = 0
        for entry in feed.entries:
            # Get title
            title = ""
            if hasattr(entry, 'title'):
                title = entry.title.lower()
            
            # Get description
            description = ""
            if hasattr(entry, 'summary'):
                description = entry.summary.lower()
            elif hasattr(entry, 'description'):
                description = entry.description.lower()
            
            # Combine title and description
            full_text = title + " " + description
            
            # Track if this article mentioned any styles
            found_in_article = False
            
            # Search for style keywords
            for style in style_keywords:
                if style in full_text:
                    style_counts[style] += 1
                    if not found_in_article:
                        articles_with_matches += 1
                        found_in_article = True
        
        print(f"   → {articles_with_matches} articles mentioned style keywords")
        
        # Small delay to be polite to servers
        time.sleep(0.5)
    
    except Exception as e:
        print(f"   ✗ Error: {str(e)[:60]}")

# Sort styles by count (highest first)
sorted_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)

# Print results
print("\n" + "=" * 70)
print("📊 RESULTS")
print("=" * 70)
print(f"✓ Successful feeds: {successful_feeds}/{len(rss_feeds)}")
print(f"✓ Total articles analyzed: {total_articles}")
print()

if total_articles > 0:
    print("🔥 TRENDING STYLES (from blog mentions):")
    print("-" * 70)
    
    found_any = False
    rank = 1
    for style, count in sorted_styles:
        if count > 0:
            emoji = "🔥" if rank <= 3 else "📈"
            print(f"  {emoji} #{rank:2d}  {style.title():<25} → {count:3d} mentions")
            found_any = True
            rank += 1
    
    if not found_any:
        print("  ⚠️  No style keywords found in articles.")

else:
    print("⚠️  No articles were found from any feed!")

# Save results to JSON file
results = {
    "source": "fashion_blog_rss",
    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "total_articles_analyzed": total_articles,
    "successful_feeds": successful_feeds,
    "total_feeds_attempted": len(rss_feeds),
    "trending_styles": [
        {"style": style, "mentions": count, "rank": i+1} 
        for i, (style, count) in enumerate(sorted_styles) if count > 0
    ]
}

output_file = 'trending_styles.json'
with open(output_file, 'w') as f:
    json.dump(results, f, indent=2)

# Also write a JS file so the leaderboard can load without a server (works on file://)
js_file = 'trending_styles_data.js'
js_content = 'window.TRENDING_STYLES = ' + json.dumps(results) + ';\n'
with open(js_file, 'w') as f:
    f.write(js_content)

print("\n" + "=" * 70)
print(f"💾 Results saved to '{output_file}' and '{js_file}'")
print("=" * 70)