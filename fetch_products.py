#!/usr/bin/env python3
"""
Outfit Generator — Product Fetcher (ScraperAPI edition)
=========================================================
Reads trending_styles.json → searches H&M, ASOS, Zara
→ writes products_data.js for the website.

Setup:
  pip install requests
  set SCRAPERAPI_KEY=your_key   (Windows CMD)
  $env:SCRAPERAPI_KEY="your_key" (PowerShell)

Run:
  python fetch_products.py
"""

import os, sys, re, json, time, random, requests
from urllib.parse import quote_plus
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────
SCRAPERAPI_KEY  = os.environ.get("SCRAPERAPI_KEY", "PUT_YOUR_KEY_HERE")
SCRAPER_URL     = "https://api.scraperapi.com/"
TOP_STYLES      = 10   # how many trending styles to build fits for

# ─────────────────────────────────────────────────────
#  SCRAPERAPI WRAPPER
# ─────────────────────────────────────────────────────

def fetch(url, render_js=False, retries=2):
    """Fetch a URL through ScraperAPI. render_js=True for JS-heavy pages (costs more credits)."""
    params = {"api_key": SCRAPERAPI_KEY, "url": url}
    if render_js:
        params["render"] = "true"
    for attempt in range(retries + 1):
        try:
            r = requests.get(SCRAPER_URL, params=params, timeout=60)
            if r.status_code == 200:
                return r
            print(f"        HTTP {r.status_code} on attempt {attempt+1}")
        except Exception as e:
            print(f"        Error attempt {attempt+1}: {str(e)[:60]}")
        if attempt < retries:
            time.sleep(3)
    return None


# ─────────────────────────────────────────────────────
#  STORE SCRAPERS
# ─────────────────────────────────────────────────────

def search_hm(query, n=3):
    """Search H&M via their internal JSON API."""
    url = (
        f"https://www2.hm.com/en_us/search-results.html"
        f"?q={quote_plus(query)}&sort=RELEVANCE&image-size=small"
        f"&image=model&offset=0&pagesize={n}&format=json"
    )
    r = fetch(url)
    if not r:
        return []
    try:
        data = r.json()
        products = data.get("products") or data.get("results") or []
        # Also try nested path
        if not products:
            products = data.get("plpList", {}).get("products", [])
        results = []
        for p in products[:n]:
            name  = p.get("name") or p.get("title") or ""
            price = p.get("price", {})
            if isinstance(price, dict):
                price = price.get("value") or price.get("price") or ""
            images = p.get("images") or p.get("swatches") or []
            image  = ""
            if images:
                first = images[0]
                if isinstance(first, dict):
                    image = first.get("url") or first.get("src") or ""
                elif isinstance(first, str):
                    image = first
            pid = p.get("code") or p.get("id") or ""
            url_p = f"https://www2.hm.com/en_us/productpage.{pid}.html" if pid else ""
            if name:
                results.append({"name": name, "price": str(price), "image": image, "url": url_p})
        return results
    except Exception:
        # Fallback: scrape the HTML page and extract __NEXT_DATA__
        return search_hm_html(query, n)


def search_hm_html(query, n=3):
    """Fallback: scrape H&M search page HTML and extract embedded product JSON."""
    url = f"https://www2.hm.com/en_us/search-results.html?q={quote_plus(query)}"
    r = fetch(url)
    if not r:
        return []
    try:
        html = r.text
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return []
        data   = json.loads(match.group(1))
        # Navigate possible paths
        page   = data.get("props", {}).get("pageProps", {})
        prods  = (page.get("searchData", {}).get("products")
               or page.get("plpData", {}).get("products")
               or page.get("products")
               or [])
        results = []
        for p in prods[:n]:
            name   = p.get("name") or p.get("title") or ""
            price  = p.get("price", {})
            if isinstance(price, dict):
                price = price.get("value") or ""
            imgs   = p.get("images") or []
            image  = imgs[0].get("url", "") if imgs and isinstance(imgs[0], dict) else (imgs[0] if imgs else "")
            pid    = p.get("code") or p.get("id") or ""
            purl   = f"https://www2.hm.com/en_us/productpage.{pid}.html" if pid else ""
            if name:
                results.append({"name": name, "price": str(price), "image": image, "url": purl})
        return results
    except Exception as e:
        print(f"        H&M HTML parse error: {str(e)[:60]}")
        return []


_ASOS_BRANDS = {
    'asos design': 'asos-design', 'jack & jones': 'jack-jones',
    '& other stories': 'other-stories', '4th & reckless': '4th-reckless',
    'new balance': 'new-balance', 'cheap monday': 'cheap-monday',
    'public desire': 'public-desire', 'reclaimed vintage': 'reclaimed-vintage',
}

def _asos_url(name, pid):
    import re
    slug = lambda s: re.sub(r'[\s]+', '-', re.sub(r'[^a-z0-9\s-]', '', s.lower()).strip())
    nl = name.lower()
    brand = next((v for k, v in sorted(_ASOS_BRANDS.items(), key=lambda x: -len(x[0])) if nl.startswith(k)), slug(name.split()[0]))
    return f"https://www.asos.com/{brand}/{slug(name)}/prd/{pid}"


def search_asos(query, n=3, gender="women"):
    """Search ASOS via their keyword search API. gender = 'men' or 'women'."""
    channel = "COM-Men" if gender == "men" else "COM-Default"
    url = (
        f"https://www.asos.com/api/product/search/v2/"
        f"?q={quote_plus(query)}&limit={n}&store=US&lang=en-US"
        f"&currency=USD&sizeSchema=US&offset=0&channel={channel}"
    )
    r = fetch(url)
    if not r:
        return []
    try:
        data     = r.json()
        products = data.get("products") or []
        results  = []
        for p in products[:n]:
            name   = p.get("name") or ""
            price  = p.get("price", {})
            if isinstance(price, dict):
                price = price.get("current", {}).get("value") or price.get("value") or ""
            imgs   = p.get("imageUrl") or ""
            if imgs and not imgs.startswith("http"):
                imgs = "https://" + imgs
            if imgs and "?" not in imgs:
                imgs += "?$n_320w$&wid=317&fit=constrain"
            # Use the actual product URL slug from the API response
            slug = p.get("url") or ""
            if slug and not slug.startswith("http"):
                purl = "https://www.asos.com/" + slug.split("#")[0]  # strip colourway hash
            elif slug.startswith("http"):
                purl = slug
            else:
                # Fallback: build URL from product name + ID
                pid = str(p.get("id") or "")
                purl = _asos_url(name, pid) if pid else ""
            if name:
                results.append({"name": name, "price": str(price), "image": imgs, "url": purl})
        return results
    except Exception as e:
        print(f"        ASOS parse error: {str(e)[:60]}")
        return []


def search_zara(query, n=3):
    """Search Zara via their internal REST API."""
    # US store ID is 11719
    url = (
        f"https://www.zara.com/itxrest/3/catalog/store/11719/search"
        f"?searchTerm={quote_plus(query)}&languageId=-1&type=product&quantity={n}"
    )
    r = fetch(url)
    if not r:
        return []
    try:
        data     = r.json()
        products = data.get("product") or data.get("products") or data.get("productGroups", [{}])[0].get("elements", []) if isinstance(data.get("productGroups"), list) else []
        results  = []
        for p in products[:n]:
            # Zara wraps in a "product" sub-object sometimes
            if "detail" in p:
                p = p["detail"]
            name   = p.get("name") or p.get("title") or ""
            price  = p.get("price") or p.get("displayPrice") or ""
            # Price is often in cents
            if isinstance(price, (int, float)) and price > 1000:
                price = f"${price/100:.2f}"
            imgs   = p.get("xmedia") or p.get("images") or []
            image  = ""
            if imgs and isinstance(imgs[0], dict):
                path = imgs[0].get("path") or ""
                name_i = imgs[0].get("name") or ""
                if path and name_i:
                    image = f"https://static.zara.net/photos//{path}/w/563/{name_i}.jpg"
                else:
                    image = imgs[0].get("url") or imgs[0].get("src") or ""
            pid    = p.get("id") or p.get("productId") or ""
            purl   = f"https://www.zara.com/us/en/{pid}.html" if pid else ""
            if name:
                results.append({"name": name, "price": str(price), "image": image, "url": purl})
        return results
    except Exception as e:
        print(f"        Zara parse error: {str(e)[:60]}")
        return []


# Store registry: tried in order, uses first that returns results
STORES = [
    {"name": "ASOS",  "color": "#2d2d2d", "fn": search_asos},
    {"name": "H&M",   "color": "#e50010", "fn": search_hm},
    {"name": "Zara",  "color": "#1a1a1a", "fn": search_zara},
]

GENDERS = ["men", "women"]


# ─────────────────────────────────────────────────────
#  STYLE → SEARCH TERMS
# ─────────────────────────────────────────────────────
STYLE_MAP = {
    "streetwear":         {"top": "oversized graphic hoodie",    "bottom": "cargo pants",             "shoes": "chunky sneakers"},
    "y2k":                {"top": "y2k crop top",                "bottom": "low rise flare jeans",    "shoes": "platform sneakers"},
    "dark academia":      {"top": "plaid oversized blazer",      "bottom": "tailored trousers",       "shoes": "oxford shoes"},
    "clean girl":         {"top": "ribbed tank top",             "bottom": "wide leg trousers",       "shoes": "white sneakers"},
    "quiet luxury":       {"top": "cashmere crewneck sweater",   "bottom": "tailored straight trousers","shoes": "leather loafers"},
    "old money":          {"top": "polo shirt",                  "bottom": "chino pants",             "shoes": "penny loafers"},
    "cottagecore":        {"top": "floral puff sleeve blouse",   "bottom": "flowy midi skirt",        "shoes": "ballet flats"},
    "grunge":             {"top": "oversized flannel shirt",     "bottom": "ripped skinny jeans",     "shoes": "chunky platform boots"},
    "gorpcore":           {"top": "technical fleece jacket",     "bottom": "ripstop cargo pants",     "shoes": "trail running shoes"},
    "minimalist":         {"top": "white fitted t-shirt",        "bottom": "straight leg jeans",      "shoes": "white leather sneakers"},
    "preppy":             {"top": "polo shirt",                  "bottom": "chino shorts",            "shoes": "loafers"},
    "athleisure":         {"top": "sports bra crop top",         "bottom": "high waist leggings",     "shoes": "running sneakers"},
    "coquette":           {"top": "bow detail satin top",        "bottom": "mini skirt",              "shoes": "ballet flats"},
    "office siren":       {"top": "tailored blazer",             "bottom": "pencil skirt",            "shoes": "pointed toe heels"},
    "balletcore":         {"top": "wrap crop top",               "bottom": "flowy skirt",             "shoes": "satin ballet flats"},
    "barbiecore":         {"top": "pink crop top",               "bottom": "pink mini skirt",         "shoes": "platform heels"},
    "mob wife":           {"top": "faux fur coat",               "bottom": "animal print skirt",      "shoes": "heeled ankle boots"},
    "tomato girl":        {"top": "linen striped top",           "bottom": "linen wide trousers",     "shoes": "strappy sandals"},
    "indie sleaze":       {"top": "vintage band graphic tee",    "bottom": "disco flare pants",       "shoes": "ankle boots"},
    "blokecore":          {"top": "soccer jersey",               "bottom": "track shorts",            "shoes": "retro trainers"},
    "boho":               {"top": "crochet top",                 "bottom": "wide leg bohemian pants", "shoes": "platform sandals"},
    "maximalist":         {"top": "printed statement blouse",    "bottom": "wide leg printed pants",  "shoes": "embellished heels"},
    "coastal grandmother":{"top": "linen button up shirt",       "bottom": "linen wide trousers",     "shoes": "espadrilles"},
    "dopamine dressing":  {"top": "bright color oversized shirt","bottom": "wide leg trousers",       "shoes": "colorful sneakers"},
    "vanilla girl":       {"top": "white ribbed top",            "bottom": "cream straight jeans",    "shoes": "white sneakers"},
    "downtown girl":      {"top": "black leather jacket",        "bottom": "straight jeans",          "shoes": "ankle boots"},
    "regencycore":        {"top": "empire waist dress top",      "bottom": "flowy skirt",             "shoes": "mary jane heels"},
    "normcore":           {"top": "basic crewneck sweatshirt",   "bottom": "straight jeans",          "shoes": "white sneakers"},
    "casual chic":        {"top": "linen relaxed shirt",         "bottom": "straight jeans",          "shoes": "loafers"},
    "business casual":    {"top": "fitted blazer",               "bottom": "tailored trousers",       "shoes": "loafers"},
    "leather":            {"top": "leather jacket",              "bottom": "leather pants",           "shoes": "leather ankle boots"},
    "denim":              {"top": "denim jacket",                "bottom": "straight jeans",          "shoes": "white sneakers"},
    "linen":              {"top": "linen button up shirt",       "bottom": "linen wide trousers",     "shoes": "espadrilles"},
    "silk":               {"top": "silk satin blouse",           "bottom": "satin slip skirt",        "shoes": "strappy heels"},
    "velvet":             {"top": "velvet blazer",               "bottom": "velvet flare trousers",   "shoes": "velvet heeled mules"},
    "animal print":       {"top": "animal print blouse",         "bottom": "black trousers",          "shoes": "ankle boots"},
    "floral":             {"top": "floral blouse",               "bottom": "denim jeans",             "shoes": "white sneakers"},
    "plaid":              {"top": "plaid blazer",                "bottom": "tailored trousers",       "shoes": "loafers"},
    "all black":          {"top": "black oversized sweater",     "bottom": "black wide leg pants",    "shoes": "black boots"},
    "all white":          {"top": "white oversized shirt",       "bottom": "white wide leg trousers", "shoes": "white sneakers"},
    "neon":               {"top": "neon oversized tee",          "bottom": "black jeans",             "shoes": "white sneakers"},
    "earth tones":        {"top": "rust brown oversized shirt",  "bottom": "camel trousers",          "shoes": "tan chunky boots"},
    "neutrals":           {"top": "beige ribbed top",            "bottom": "cream wide trousers",     "shoes": "nude loafers"},
    "pastels":            {"top": "pastel pink top",             "bottom": "pastel wide trousers",    "shoes": "white sneakers"},
    "oversized":          {"top": "oversized sweater",           "bottom": "wide leg jeans",          "shoes": "chunky sneakers"},
    "baggy":              {"top": "baggy graphic tee",           "bottom": "baggy wide jeans",        "shoes": "chunky sneakers"},
    "wide leg":           {"top": "fitted crop top",             "bottom": "wide leg trousers",       "shoes": "platform boots"},
    "high rise":          {"top": "tucked in shirt",             "bottom": "high rise wide leg jeans","shoes": "ankle boots"},
    "low rise":           {"top": "fitted crop top",             "bottom": "low rise straight jeans", "shoes": "platform sneakers"},
    "vintage":            {"top": "vintage oversized blazer",    "bottom": "high waist straight jeans","shoes": "platform loafers"},
    "sustainable fashion":{"top": "organic cotton tee",          "bottom": "wide leg jeans",          "shoes": "canvas sneakers"},
    "gender neutral":     {"top": "oversized button up shirt",   "bottom": "wide straight trousers",  "shoes": "chunky sneakers"},
    "spring fashion":     {"top": "floral printed shirt",        "bottom": "wide leg trousers",       "shoes": "strappy sandals"},
    "summer style":       {"top": "linen crop top",              "bottom": "linen shorts",            "shoes": "platform sandals"},
    "fall fashion":       {"top": "oversized knit sweater",      "bottom": "straight jeans",          "shoes": "ankle boots"},
    "winter style":       {"top": "wool coat",                   "bottom": "straight trousers",       "shoes": "knee high boots"},
}


def get_searches(style):
    if style in STYLE_MAP:
        return STYLE_MAP[style]
    return {"top": f"{style} top", "bottom": f"{style} pants", "shoes": f"{style} shoes"}


# ─────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────

def main():
    if SCRAPERAPI_KEY == "PUT_YOUR_KEY_HERE":
        print("ERROR: Set your ScraperAPI key first!")
        print("  Windows CMD:   set SCRAPERAPI_KEY=xxxx")
        print("  PowerShell:    $env:SCRAPERAPI_KEY='xxxx'")
        return

    print("=" * 65)
    print("OUTFIT GENERATOR — PRODUCT FETCHER  (ASOS + H&M + Zara)")
    print("Using: ScraperAPI")
    print("=" * 65)

    # Load trending styles
    try:
        with open("trending_styles.json") as f:
            trending = json.load(f)
        top_styles = [s["style"] for s in trending.get("trending_styles", [])[:TOP_STYLES]]
        print(f"\nTrending: {', '.join(top_styles)}\n")
    except FileNotFoundError:
        print("trending_styles.json not found — using built-in style list")
        top_styles = list(STYLE_MAP.keys())[:TOP_STYLES]

    fits = []

    for style in top_styles:
        searches = get_searches(style)
        auto     = style not in STYLE_MAP
        gender   = random.choice(GENDERS)
        print(f"\n-- {style.upper()} [{gender}] {'[auto]' if auto else ''}")

        fit_items = {}
        for slot in ["top", "bottom", "shoes"]:
            query = searches[slot]
            print(f"  {slot}: '{query}'")

            for store in STORES:
                print(f"    [{store['name']}]...", end=" ", flush=True)
                # Pass gender to ASOS; H&M/Zara use the query as-is
                if store["name"] == "ASOS":
                    products = store["fn"](query, gender=gender)
                else:
                    products = store["fn"](query)
                if products:
                    p = products[0]
                    p["slot"]       = slot
                    p["store"]      = store["name"]
                    p["storeColor"] = store["color"]
                    fit_items[slot] = p
                    print(f"got: {p['name'][:40]}")
                    break
                else:
                    print("no results")

            if slot not in fit_items:
                print(f"    nothing found for {slot}")

        if len(fit_items) >= 2:
            fits.append({
                "style": style,
                "gender": gender,
                "items": [fit_items.get("top"), fit_items.get("bottom"), fit_items.get("shoes")],
            })
            print(f"  Fit built ({len(fit_items)}/3 items)")
        else:
            print(f"  Not enough items — skipping")

    output = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fits": fits,
    }

    with open("products_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    with open("products_data.js", "w", encoding="utf-8") as f:
        f.write("window.OUTFIT_PRODUCTS = " + json.dumps(output) + ";\n")

    print("\n" + "=" * 65)
    print(f"Built {len(fits)} fits")
    print(f"Saved products_data.json + products_data.js")
    print("=" * 65)


if __name__ == "__main__":
    main()
