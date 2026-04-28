#!/usr/bin/env python3
"""
Outfit Generator — Product Fetcher (RapidAPI H&M edition)
==========================================================
Reads trending_styles.json → searches H&M via RapidAPI
→ writes products_data.js for the website.

Setup:
  pip install requests

Run:
  python fetch_products.py
"""

import sys, json, requests, itertools, os
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────────────
RAPIDAPI_KEY   = os.environ.get("RAPIDAPI_KEY")
if not RAPIDAPI_KEY:
    print("ERROR: RAPIDAPI_KEY environment variable not set.")
    print("See README.md for setup instructions.")
    sys.exit(1)
HM_HOST        = "h-m-hennes-mauritz.p.rapidapi.com"
HM_HEADERS     = {"X-RapidAPI-Key": RAPIDAPI_KEY, "X-RapidAPI-Host": HM_HOST}
CANDIDATES     = 15   # how many H&M products to fetch per slot query
FITS_PER_COMBO = 4    # distinct fits to build per style+gender combo


# ─────────────────────────────────────────────────────
#  H&M SEARCH
# ─────────────────────────────────────────────────────

def search_hm(query, n=15):
    try:
        r = requests.get(
            f"https://{HM_HOST}/search",
            headers=HM_HEADERS,
            params={"query": query, "country": "us", "lang": "en",
                    "pageSize": str(n), "pageNumber": "0"},
            timeout=20,
        )
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}")
            return []
        data = r.json()
        products = (data.get("data") or {}).get("products") or []
        if not products and isinstance(data.get("data"), list):
            products = data["data"]
        results = []
        for p in products[:n]:
            name      = p.get("productName") or p.get("name") or ""
            price     = ""
            prices    = p.get("prices") or []
            if prices:
                price = prices[0].get("formattedPrice") or str(prices[0].get("price") or "")
            images    = p.get("images") or []
            image     = images[0].get("url") if images else (p.get("productImage") or "")
            url       = p.get("url") or ""
            color_name = p.get("colorName") or ""
            if name:
                results.append({
                    "name": name, "colorName": color_name,
                    "price": price, "image": image,
                    "url": url, "store": "H&M", "storeColor": "#e50010",
                })
        return results
    except Exception as e:
        print(f"  error: {str(e)[:80]}")
        return []


# ─────────────────────────────────────────────────────
#  IMPROVED COLOR MATCHING
# ─────────────────────────────────────────────────────
COLOR_DB = {
    "black":    (0,   0,   8),   "white":    (0,   0,  96),
    "grey":     (0,   0,  50),   "gray":     (0,   0,  50),
    "charcoal": (0,   0,  22),   "silver":   (0,   0,  68),
    "navy":     (225, 68, 18),   "blue":     (210, 72, 48),
    "denim":    (212, 40, 45),   "cobalt":   (215, 80, 40),
    "red":      (2,   78, 48),   "burgundy": (344, 58, 28),
    "maroon":   (0,   58, 24),   "wine":     (348, 60, 26),
    "pink":     (340, 65, 68),   "blush":    (352, 50, 80),
    "rose":     (350, 60, 55),   "coral":    (14,  78, 63),
    "orange":   (22,  78, 52),   "rust":     (14,  63, 42),
    "yellow":   (52,  88, 58),   "gold":     (44,  68, 58),
    "green":    (122, 45, 38),   "olive":    (72,  43, 33),
    "sage":     (98,  22, 52),   "mint":     (154, 43, 68),
    "teal":     (174, 52, 38),   "emerald":  (145, 55, 35),
    "purple":   (268, 58, 48),   "lavender": (270, 48, 73),
    "lilac":    (280, 42, 72),   "plum":     (300, 45, 30),
    "brown":    (24,  43, 28),   "tan":      (33,  43, 53),
    "camel":    (33,  52, 53),   "beige":    (40,  28, 78),
    "cream":    (44,  28, 88),   "ecru":     (43,  25, 82),
    "khaki":    (55,  28, 58),   "sand":     (38,  32, 72),
    "stone":    (40,  18, 62),   "ivory":    (45,  30, 92),
    "taupe":    (35,  15, 55),   "mocha":    (25,  30, 38),
}

def get_color(product):
    for field in ["colorName", "name"]:
        s = (product.get(field) or "").lower()
        for key in sorted(COLOR_DB, key=len, reverse=True):
            if key in s:
                return COLOR_DB[key]
    return None

def is_neutral(hsl):
    return hsl[1] < 20

def hue_diff(h1, h2):
    return min(abs(h1 - h2), 360 - abs(h1 - h2))

def pair_score(c1, c2):
    """
    Improved color harmony scorer.
    Considers: monochromatic, analogous, split-complementary,
    complementary, triadic, lightness contrast for neutrals.
    """
    if c1 is None or c2 is None:
        return 0.75  # unknown color → neutral assumption

    n1, n2 = is_neutral(c1), is_neutral(c2)

    # Both neutrals — good if lightness contrasts, risky if same
    if n1 and n2:
        l_diff = abs(c1[2] - c2[2])
        if l_diff >= 30: return 1.00   # black + white, charcoal + cream etc.
        if l_diff >= 15: return 0.90   # moderate contrast
        return 0.72                    # same-ish neutrals (grey + grey) → a bit flat

    # One neutral anchors the palette — almost always works
    if n1 or n2:
        return 0.97

    # Both chromatic — evaluate hue relationship
    diff = hue_diff(c1[0], c2[0])

    # Lightness contrast bonus (dark + light chromatic = more visual interest)
    l_contrast = abs(c1[2] - c2[2])
    l_bonus = 0.04 if l_contrast > 25 else 0.0

    # Saturation harmony bonus (matched saturation looks intentional)
    s_diff = abs(c1[1] - c2[1])
    s_bonus = 0.03 if s_diff < 20 else 0.0

    if diff <= 15:
        # Very close hues (near-monochromatic) — good only with l/s variation
        if l_contrast > 20 or s_diff > 25: return 0.88 + l_bonus
        return 0.68                    # too similar = muddy

    if diff <= 40:  return 0.87 + l_bonus + s_bonus   # analogous
    if diff <= 60:  return 0.80 + l_bonus              # wide analogous

    if 150 <= diff <= 170: return 0.85 + l_bonus       # split-complementary low
    if 170 <  diff <= 190: return 0.89 + l_bonus       # true complementary
    if 190 <  diff <= 210: return 0.85 + l_bonus       # split-complementary high

    if 110 <= diff <= 130: return 0.78 + l_bonus       # triadic
    if  80 <= diff <= 110: return 0.55                 # intermediate — risky
    return 0.38                                        # colour clash

def score_combo(items):
    """
    Weighted pair scoring.
    Top ↔ Bottom is the hero pairing (3×).
    Shoes ↔ Top/Bottom is supporting (1.5×).
    Outer ↔ everything is context (1×).
    """
    slot_of = {i: item.get("slot", "") for i, item in enumerate(items)}
    colors  = [get_color(item) for item in items]
    pairs   = list(itertools.combinations(range(len(items)), 2))
    if not pairs:
        return 0.75

    total, weight_sum = 0.0, 0.0
    for i, j in pairs:
        s1, s2 = slot_of[i], slot_of[j]
        c1, c2 = colors[i],  colors[j]
        sc = pair_score(c1, c2)

        if {s1, s2} == {"top", "bottom"}:       w = 3.0
        elif "shoes" in {s1, s2}:                w = 1.5
        elif "outer" in {s1, s2}:                w = 1.2
        else:                                    w = 1.0

        total      += sc * w
        weight_sum += w

    return total / weight_sum if weight_sum else 0.75


# ─────────────────────────────────────────────────────
#  DIVERSE COMBO BUILDER
#  Each successive fit removes used items so clothes don't repeat
# ─────────────────────────────────────────────────────

def build_diverse_combos(slot_candidates, n=4):
    """
    Build up to n combos where each combo uses different clothing items.
    After each pick, remove used items from the pool.
    """
    slots = [s for s in ["outer", "top", "bottom", "shoes"] if s in slot_candidates]
    # working copy — we'll drain this
    pool = {s: list(slot_candidates[s]) for s in slots}
    selected = []

    for _ in range(n):
        # need at least 1 candidate in every required slot
        required = [s for s in slots if s != "outer"]
        if not all(pool.get(s) for s in required):
            break

        # score all remaining combos
        best_score, best_combo = -1, None
        active = {s: pool[s] for s in slots if pool.get(s)}
        for combo in itertools.product(*[active[s] for s in active]):
            items = list(combo)
            sc = score_combo(items)
            if sc > best_score:
                best_score = sc
                best_combo = {list(active.keys())[i]: items[i]
                               for i in range(len(items))}

        if best_combo is None:
            break

        selected.append((best_score, best_combo))

        # drain used items from pool
        for s, item in best_combo.items():
            pool[s] = [p for p in pool[s] if p.get("name") != item.get("name")]

    return selected


# ─────────────────────────────────────────────────────
#  STYLE → SEARCH TERMS
#  Multiple query variants per slot → more unique candidates
# ─────────────────────────────────────────────────────
STYLE_MAP = {
    # ── 4-piece (outer + top + bottom + shoes) ──────────────────────
    "streetwear": {
        "outer":  ["bomber jacket", "track jacket", "windbreaker"],
        "top":    ["graphic tee oversized", "printed hoodie", "logo sweatshirt"],
        "bottom": ["cargo pants", "baggy jeans", "joggers"],
        "shoes":  ["chunky sneakers", "high top sneakers", "basketball shoes"],
    },
    "dark academia": {
        "outer":  ["plaid blazer", "tweed coat", "corduroy blazer"],
        "top":    ["turtleneck knit", "cable knit sweater", "fitted button shirt"],
        "bottom": ["tailored trousers", "plaid trousers", "straight chinos"],
        "shoes":  ["oxford shoes", "chelsea boots", "loafers"],
    },
    "old money": {
        "outer":  ["wool blazer", "single breasted blazer", "cashmere coat"],
        "top":    ["polo shirt", "oxford shirt", "linen shirt"],
        "bottom": ["chino pants", "tailored trousers", "straight trousers"],
        "shoes":  ["penny loafers", "tasseled loafers", "leather loafers"],
    },
    "grunge": {
        "outer":  ["flannel shirt oversized", "denim jacket oversized", "plaid overshirt"],
        "top":    ["band tee", "graphic tee black", "oversized tee faded"],
        "bottom": ["ripped skinny jeans", "ripped black jeans", "wide leg jeans"],
        "shoes":  ["platform boots", "chunky boots", "high top boots"],
    },
    "preppy": {
        "outer":  ["navy blazer", "varsity jacket", "quilted jacket"],
        "top":    ["polo shirt", "striped rugby shirt", "oxford button shirt"],
        "bottom": ["chino shorts", "slim chinos", "pleated trousers"],
        "shoes":  ["loafers", "boat shoes", "white tennis shoes"],
    },
    "gorpcore": {
        "outer":  ["waterproof jacket shell", "puffer jacket", "fleece zip jacket"],
        "top":    ["fleece pullover", "thermal long sleeve", "performance t-shirt"],
        "bottom": ["cargo hiking pants", "ripstop pants", "track pants"],
        "shoes":  ["trail running shoes", "hiking boots", "technical sneakers"],
    },
    "business casual": {
        "outer":  ["tailored blazer", "single breasted suit jacket", "structured blazer"],
        "top":    ["button up oxford shirt", "dress shirt", "linen shirt"],
        "bottom": ["tailored trousers slim", "suit trousers", "chino trousers"],
        "shoes":  ["loafers", "oxford leather shoes", "derby shoes"],
    },
    "quiet luxury": {
        "outer":  ["cashmere coat", "long wool coat", "camel coat"],
        "top":    ["ribbed turtleneck", "merino sweater", "cashmere jumper"],
        "bottom": ["tailored straight trousers", "wide leg trousers", "straight leg pants"],
        "shoes":  ["leather loafers", "pointed flats", "suede loafers"],
    },
    "minimalist": {
        "outer":  ["light trench coat", "simple blazer", "linen blazer"],
        "top":    ["white fitted t-shirt", "ribbed tank top", "simple long sleeve"],
        "bottom": ["straight leg jeans", "straight leg trousers", "slim chinos"],
        "shoes":  ["white leather sneakers", "minimalist sneakers", "clean sneakers"],
    },
    "mob wife": {
        "outer":  ["faux fur coat", "fur trim coat", "oversized fur jacket"],
        "top":    ["satin blouse", "corset top", "bodysuit"],
        "bottom": ["leather skirt", "animal print skirt", "wide leg leather pants"],
        "shoes":  ["heeled ankle boots", "strappy heels", "platform boots"],
    },
    "vintage": {
        "outer":  ["trench coat", "denim jacket vintage", "corduroy jacket"],
        "top":    ["retro graphic tee", "vintage band tee", "fitted polo"],
        "bottom": ["high waist straight jeans", "flared jeans", "corduroy pants"],
        "shoes":  ["platform loafers", "chunky loafers", "retro sneakers"],
    },

    # ── 3-piece (top + bottom + shoes) ──────────────────────────────
    "y2k": {
        "top":    ["crop top", "butterfly top", "velour top"],
        "bottom": ["flare jeans low rise", "mini skirt", "velour pants"],
        "shoes":  ["platform sneakers", "platform sandals", "chunky shoes"],
    },
    "clean girl": {
        "top":    ["ribbed tank top", "fitted crop top", "fitted cami"],
        "bottom": ["wide leg trousers", "linen pants wide", "tailored wide pants"],
        "shoes":  ["white sneakers", "pointed flats", "mule sandals"],
    },
    "cottagecore": {
        "top":    ["floral puff sleeve blouse", "broderie blouse", "smocked top"],
        "bottom": ["flowy midi skirt", "floral midi skirt", "linen midi skirt"],
        "shoes":  ["ballet flats", "flat sandals", "lace up boots"],
    },
    "athleisure": {
        "top":    ["sports bra", "cropped hoodie", "performance tank top"],
        "bottom": ["high waist leggings", "bike shorts", "wide leg joggers"],
        "shoes":  ["running sneakers", "chunky white sneakers", "slip on sneakers"],
    },
    "coquette": {
        "top":    ["satin bow top", "lace corset top", "ribbon tie blouse"],
        "bottom": ["mini skirt satin", "pleated mini skirt", "ruffle mini skirt"],
        "shoes":  ["ballet flats", "mary jane shoes", "kitten heel mules"],
    },
    "balletcore": {
        "top":    ["wrap crop top", "ballet wrap top", "fitted cardigan wrap"],
        "bottom": ["flowy tulle skirt", "satin midi skirt", "pleated skirt"],
        "shoes":  ["ballet flats", "ribbon ballet shoes", "satin flats"],
    },
    "barbiecore": {
        "top":    ["pink crop top", "hot pink blouse", "pink fitted tee"],
        "bottom": ["pink mini skirt", "pink midi skirt", "pink wide leg pants"],
        "shoes":  ["platform heels pink", "pink mules", "white platform shoes"],
    },
    "office siren": {
        "top":    ["tailored blazer fitted", "structured blazer", "button blazer"],
        "bottom": ["pencil skirt", "tailored midi skirt", "high waist trousers"],
        "shoes":  ["pointed toe heels", "kitten heels", "strappy heeled sandals"],
    },
    "indie sleaze": {
        "top":    ["vintage graphic tee", "band t-shirt", "oversized shirt"],
        "bottom": ["disco pants", "flare pants", "skinny jeans black"],
        "shoes":  ["ankle boots", "high top converse", "platform boots"],
    },
    "boho": {
        "top":    ["crochet top", "smocked blouse peasant", "fringe top"],
        "bottom": ["wide leg flowy pants", "maxi skirt", "floral wide leg"],
        "shoes":  ["platform sandals", "strappy flat sandals", "espadrilles"],
    },
    "linen": {
        "top":    ["linen shirt", "linen button up", "linen crop top"],
        "bottom": ["linen trousers", "linen wide pants", "linen shorts"],
        "shoes":  ["leather sandals", "canvas espadrilles", "flat mules"],
    },
    "all black": {
        "top":    ["black oversized hoodie", "black knit sweater", "black long sleeve"],
        "bottom": ["black wide leg pants", "black straight jeans", "black cargo pants"],
        "shoes":  ["black boots chelsea", "black chunky sneakers", "black ankle boots"],
    },
    "all white": {
        "top":    ["white fitted top", "white linen shirt", "white ribbed tee"],
        "bottom": ["white trousers", "white wide leg pants", "white jeans"],
        "shoes":  ["white sneakers", "white mules", "white sandals"],
    },
    "denim": {
        "top":    ["denim jacket", "denim shirt", "denim vest"],
        "bottom": ["straight jeans", "wide leg jeans", "flared jeans"],
        "shoes":  ["white sneakers", "loafers", "ankle boots"],
    },
    "oversized": {
        "top":    ["oversized sweater", "oversized hoodie", "oversized blazer"],
        "bottom": ["wide leg jeans", "baggy cargo pants", "straight leg trousers"],
        "shoes":  ["chunky sneakers", "dad sneakers", "platform sneakers"],
    },
    "stripes": {
        "top":    ["striped shirt", "striped button shirt", "striped blouse"],
        "bottom": ["straight trousers", "wide leg trousers", "straight jeans"],
        "shoes":  ["loafers", "white sneakers", "ballet flats"],
    },
    "velvet": {
        "top":    ["velvet blazer", "velvet top", "velvet blouse"],
        "bottom": ["velvet trousers", "velvet skirt", "velvet flare pants"],
        "shoes":  ["heeled boots", "pointed heels", "strappy sandals"],
    },
    "mesh": {
        "top":    ["mesh top", "sheer blouse", "mesh long sleeve"],
        "bottom": ["satin skirt", "midi slip skirt", "wide leg satin pants"],
        "shoes":  ["heeled sandals", "strappy heels", "kitten heel mules"],
    },
    "silk": {
        "top":    ["satin blouse", "silk cami top", "satin slip top"],
        "bottom": ["satin slip skirt", "silk midi skirt", "satin wide leg pants"],
        "shoes":  ["strappy heels", "kitten mules", "block heel sandals"],
    },
    "baggy": {
        "top":    ["oversized graphic tee", "baggy hoodie", "printed oversized shirt"],
        "bottom": ["baggy jeans", "wide leg cargo", "relaxed fit pants"],
        "shoes":  ["chunky sneakers", "retro sneakers", "high top sneakers"],
    },
    "floral": {
        "top":    ["floral blouse", "floral printed top", "floral shirt"],
        "bottom": ["straight jeans", "wide leg trousers", "midi skirt plain"],
        "shoes":  ["white sneakers", "loafers", "flat sandals"],
    },
    "gender neutral": {
        "top":    ["oversized t-shirt", "relaxed fit shirt", "simple crewneck"],
        "bottom": ["straight leg jeans", "straight chinos", "relaxed trousers"],
        "shoes":  ["chunky sneakers", "white sneakers", "loafers"],
    },
    "high rise": {
        "top":    ["fitted shirt", "cropped knit top", "fitted tank"],
        "bottom": ["high rise wide leg jeans", "high waist trousers", "high waist flare"],
        "shoes":  ["ankle boots", "loafers", "block heel shoes"],
    },
    "normcore": {
        "top":    ["crewneck sweatshirt", "plain t-shirt", "simple polo"],
        "bottom": ["straight jeans", "chino pants", "relaxed jeans"],
        "shoes":  ["white sneakers", "canvas sneakers", "clean trainers"],
    },
    "casual chic": {
        "top":    ["linen relaxed shirt", "fitted blouse", "simple knit top"],
        "bottom": ["straight jeans", "wide leg trousers", "tailored shorts"],
        "shoes":  ["loafers", "white leather sneakers", "ankle strap sandals"],
    },
    "tomato girl": {
        "top":    ["linen striped top", "red linen blouse", "strappy sun top"],
        "bottom": ["linen trousers wide", "midi skirt linen", "flowy skirt"],
        "shoes":  ["strappy sandals flat", "espadrilles", "leather sandals"],
    },
    "blokecore": {
        "top":    ["soccer jersey", "football shirt", "sports jersey"],
        "bottom": ["track shorts", "athletic shorts", "joggers"],
        "shoes":  ["trainers", "retro sneakers", "football trainers"],
    },
    "coastal grandmother": {
        "top":    ["linen button shirt", "striped linen blouse", "relaxed knit top"],
        "bottom": ["linen wide trousers", "linen wide pants", "linen skirt midi"],
        "shoes":  ["espadrilles", "leather flat sandals", "loafers"],
    },
    "maximalist": {
        "top":    ["printed blouse bold", "colorful oversized shirt", "patterned top"],
        "bottom": ["wide leg printed pants", "bold pattern skirt", "colorful trousers"],
        "shoes":  ["heeled mules", "platform sandals", "embellished flats"],
    },
    "earth tones": {
        "top":    ["brown oversized shirt", "rust knit sweater", "camel top"],
        "bottom": ["camel trousers", "olive cargo pants", "brown wide pants"],
        "shoes":  ["chunky boots brown", "tan ankle boots", "camel loafers"],
    },
    "neon": {
        "top":    ["printed oversized tee bright", "neon color top", "color block shirt"],
        "bottom": ["black jeans slim", "black wide pants", "black shorts"],
        "shoes":  ["white chunky sneakers", "neon sneakers", "colorful trainers"],
    },
}


# ─────────────────────────────────────────────────────
#  FETCH CANDIDATES WITH MULTIPLE QUERIES
# ─────────────────────────────────────────────────────

def fetch_slot_candidates(queries, gender_suffix, n_per_query=8):
    """
    Run multiple search queries for one slot, combine results,
    deduplicate by name, attach slot label.
    """
    seen_names = set()
    all_products = []
    for q in queries:
        full_query = f"{q} {gender_suffix}"
        products = search_hm(full_query, n=n_per_query)
        for p in products:
            name_key = p.get("name", "").lower().strip()
            if name_key and name_key not in seen_names:
                seen_names.add(name_key)
                all_products.append(p)
    return all_products


# ─────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────

def main():
    print("=" * 65)
    print("OUTFIT GENERATOR — PRODUCT FETCHER  (RapidAPI H&M)")
    print("=" * 65)

    fits = []
    item_order = ["outer", "top", "bottom", "shoes"]
    required_slots = ["top", "bottom", "shoes"]

    for style, slot_queries in STYLE_MAP.items():
        for gender in ["men", "women"]:
            gender_suffix = "men" if gender == "men" else "women"
            print(f"\n{'─'*55}")
            print(f"  {style.upper()} [{gender}]")

            candidates = {}
            for slot, queries in slot_queries.items():
                if isinstance(queries, str):
                    queries = [queries]
                n_per = max(4, CANDIDATES // len(queries))
                print(f"    {slot}: {queries[0]}...", end=" ", flush=True)
                products = fetch_slot_candidates(queries, gender_suffix, n_per_query=n_per)
                if products:
                    for p in products:
                        p["slot"] = slot
                    candidates[slot] = products
                    print(f"{len(products)} unique items")
                else:
                    print("no results")

            if not all(candidates.get(s) for s in required_slots):
                print(f"    ✗ skipped — missing slot")
                continue

            combos = build_diverse_combos(candidates, n=FITS_PER_COMBO)
            print(f"    → {len(combos)} fits built")
            for idx, (score, combo) in enumerate(combos):
                items = [combo[s] for s in item_order if s in combo]
                names = " + ".join(i["name"][:22] for i in items)
                print(f"      fit {idx+1}: score={score:.2f}  {names}")
                fits.append({
                    "style":      style,
                    "gender":     gender,
                    "colorScore": round(score, 2),
                    "items":      items,
                })

    output = {
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "fits": fits,
    }

    with open("products_data.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    with open("products_data.js", "w", encoding="utf-8") as f:
        f.write("window.OUTFIT_PRODUCTS = " + json.dumps(output) + ";\n")

    print("\n" + "=" * 65)
    print(f"  Done — {len(fits)} fits saved to products_data.js")
    print("=" * 65)


if __name__ == "__main__":
    main()
