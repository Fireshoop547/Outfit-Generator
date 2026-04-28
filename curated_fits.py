#!/usr/bin/env python3
"""
Curated fits — 5 men + 5 women, color-coordinated, trend-independent.
Appends to existing products_data.js.
"""
import sys, json, requests, itertools, os
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("ERROR: RAPIDAPI_KEY environment variable not set.")
    print("See README.md for setup instructions.")
    sys.exit(1)
HM_HOST      = "h-m-hennes-mauritz.p.rapidapi.com"
HM_HEADERS   = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": HM_HOST}

# ── COLOR MATCHING ──
COLOR_DB = {
    "black":    (0,   0,   8),  "white":    (0,   0,  96),
    "grey":     (0,   0,  50),  "gray":     (0,   0,  50),
    "charcoal": (0,   0,  22),  "navy":     (225, 68, 18),
    "blue":     (210, 72, 48),  "denim":    (212, 40, 45),
    "red":      (2,   78, 48),  "burgundy": (344, 58, 28),
    "pink":     (340, 65, 68),  "blush":    (352, 50, 80),
    "coral":    (14,  78, 63),  "orange":   (22,  78, 52),
    "rust":     (14,  63, 42),  "yellow":   (52,  88, 58),
    "green":    (122, 45, 38),  "olive":    (72,  43, 33),
    "sage":     (98,  22, 52),  "teal":     (174, 52, 38),
    "purple":   (268, 58, 48),  "lavender": (270, 48, 73),
    "brown":    (24,  43, 28),  "tan":      (33,  43, 53),
    "camel":    (33,  52, 53),  "beige":    (40,  28, 78),
    "cream":    (44,  28, 88),  "ecru":     (43,  25, 82),
    "khaki":    (55,  28, 58),
}

def get_color(product):
    for field in ["colorName", "name"]:
        s = (product.get(field) or "").lower()
        for key in sorted(COLOR_DB, key=len, reverse=True):
            if key in s:
                return COLOR_DB[key]
    return None

def is_neutral(hsl): return hsl[1] < 18

def pair_score(c1, c2):
    if not c1 or not c2: return 0.78
    if is_neutral(c1) or is_neutral(c2): return 1.0
    diff = min(abs(c1[0]-c2[0]), 360-abs(c1[0]-c2[0]))
    if diff < 25:  return 0.93
    if diff < 55:  return 0.88
    if 155 < diff < 205: return 0.82
    if 105 < diff < 135: return 0.72
    return 0.42

def score_combo(items):
    colors = [get_color(i) for i in items]
    pairs = list(itertools.combinations(colors, 2))
    return sum(pair_score(a, b) for a, b in pairs) / len(pairs) if pairs else 0.78

def best_combo(slot_candidates):
    slots = list(slot_candidates.keys())
    best, best_score = None, -1
    for combo in itertools.product(*[slot_candidates[s] for s in slots]):
        sc = score_combo(list(combo))
        if sc > best_score:
            best_score = sc
            best = {slots[i]: combo[i] for i in range(len(slots))}
    return best, best_score

def search_hm(query, n=5):
    try:
        r = requests.get(f"https://{HM_HOST}/search", headers=HM_HEADERS,
            params={"query": query, "country": "us", "lang": "en", "pageSize": str(n), "pageNumber": "0"},
            timeout=20)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return []
        data = r.json()
        products = (data.get("data") or {}).get("products") or []
        results = []
        for p in products[:n]:
            name  = p.get("productName") or ""
            prices = p.get("prices") or []
            price = prices[0].get("formattedPrice") if prices else ""
            images = p.get("images") or []
            image  = images[0].get("url") if images else (p.get("productImage") or "")
            url    = p.get("url") or ""
            color_name = p.get("colorName") or ""
            if name:
                results.append({"name": name, "colorName": color_name, "price": price,
                                 "image": image, "url": url, "store": "H&M", "storeColor": "#e50010"})
        return results
    except Exception as e:
        print(f"  error: {e}")
        return []

def fetch_fit(label, gender, slots):
    """slots = {slot_name: search_query}"""
    print(f"\n{label} [{gender}]")
    candidates = {}
    for slot, query in slots.items():
        print(f"  {slot}: {query}...", end=" ", flush=True)
        results = search_hm(query, n=5)
        if results:
            for r in results: r["slot"] = slot
            candidates[slot] = results
            print(f"{len(results)} options")
        else:
            print("no result")
    required = ["top", "bottom", "shoes"]
    if not all(candidates.get(s) for s in required):
        print("  Skipped — missing slot")
        return None
    combo, score = best_combo(candidates)
    order = ["outer", "top", "bottom", "shoes"]
    items = [combo[s] for s in order if s in combo]
    print(f"  Score: {score:.2f} | {' + '.join(i['name'][:22] for i in items)}")
    return {"style": label.lower(), "gender": gender, "colorScore": round(score, 2), "items": items}

# ── CURATED FITS ──
CURATED = [
    # ── MEN ──
    ("Navy & White Classic",  "men", {
        "outer":  "navy blazer men",
        "top":    "white oxford shirt men",
        "bottom": "dark wash straight jeans men",
        "shoes":  "white leather sneakers men",
    }),
    ("Earth Tones",           "men", {
        "outer":  "camel overcoat men",
        "top":    "cream knit sweater men",
        "bottom": "olive trousers men",
        "shoes":  "tan suede boots men",
    }),
    ("All Black Sharp",       "men", {
        "outer":  "black wool coat men",
        "top":    "black turtleneck men",
        "bottom": "black slim trousers men",
        "shoes":  "black chelsea boots men",
    }),
    ("Grey & Denim Casual",   "men", {
        "top":    "grey crewneck sweatshirt men",
        "bottom": "dark indigo straight jeans men",
        "shoes":  "white chunky sneakers men",
    }),
    ("Burgundy & Tan Warm",   "men", {
        "outer":  "burgundy jacket men",
        "top":    "beige crewneck men",
        "bottom": "dark wash straight jeans men",
        "shoes":  "brown leather boots men",
    }),
    # ── WOMEN ──
    ("Monochrome Beige",      "women", {
        "outer":  "beige trench coat women",
        "top":    "white fitted top women",
        "bottom": "beige wide leg trousers women",
        "shoes":  "white sneakers women",
    }),
    ("Navy & Cream",          "women", {
        "top":    "cream ribbed knit top women",
        "bottom": "navy wide leg trousers women",
        "shoes":  "white sneakers women",
    }),
    ("Olive & White",         "women", {
        "outer":  "olive green jacket women",
        "top":    "white ribbed top women",
        "bottom": "straight leg jeans women",
        "shoes":  "white sneakers women",
    }),
    ("Blush Pink Soft",       "women", {
        "top":    "blush pink knit top women",
        "bottom": "white wide leg trousers women",
        "shoes":  "ballet flats women",
    }),
    ("All Black Power",       "women", {
        "outer":  "black blazer women",
        "top":    "black fitted top women",
        "bottom": "black wide leg trousers women",
        "shoes":  "black heeled boots women",
    }),
]

def main():
    print("=" * 60)
    print("CURATED FITS — 5 men + 5 women")
    print("=" * 60)

    new_fits = []
    for label, gender, slots in CURATED:
        fit = fetch_fit(label, gender, slots)
        if fit:
            new_fits.append(fit)

    # Load existing products_data.json if present
    try:
        with open("products_data.json") as f:
            existing = json.load(f)
        all_fits = existing.get("fits", []) + new_fits
    except FileNotFoundError:
        all_fits = new_fits

    output = {"generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "fits": all_fits}

    with open("products_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    with open("products_data.js", "w", encoding="utf-8") as f:
        f.write("window.OUTFIT_PRODUCTS = " + json.dumps(output) + ";\n")

    print(f"\n{'='*60}")
    print(f"Added {len(new_fits)} curated fits — total {len(all_fits)} fits saved")
    print("=" * 60)

if __name__ == "__main__":
    main()
