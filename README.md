# Outfit Generator

A dark-themed web app that generates outfit recommendations based on trending fashion styles and real product data from H&M, ASOS, and Zara.

## Features

- **Home Tab**: Browse trending fashion styles from 26+ RSS feeds
- **Generator Tab**: View AI-curated outfits with real product links
- **Styles Tab**: Explore style profiles and color palettes
- Dark theme with custom animated cursor
- Real product integration via Apify/RapidAPI scrapers

## Setup

### Prerequisites

- Python 3.7+
- `requests` library: `pip install requests`

### API Keys

This project uses external APIs to fetch real product data. You need to get free API keys:

1. **RapidAPI (for H&M products)** — Required
   - Go to: https://rapidapi.com/
   - Search for "H&M" or "Hennes & Mauritz"
   - Subscribe to the free tier (gives you free API calls)
   - Copy your API key

2. **ScraperAPI** — Optional (fallback scraper)
   - Go to: https://www.scraperapi.com/
   - Sign up for free tier
   - Copy your API key

### Installation

1. Clone the repo
2. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env   # Linux/Mac
   copy .env.example .env # Windows
   ```
3. Edit `.env` and paste your API keys:
   ```
   RAPIDAPI_KEY=your_actual_key_here
   SCRAPERAPI_KEY=your_actual_key_here  # optional
   ```
4. Run a data script to fetch products:
   ```bash
   python fetch_products.py      # Main fetcher (recommended)
   python curated_fits.py        # Add curated fits
   python rebuild_products.py    # Use local fallback data
   ```
5. Open `index.html` in your browser

## Scripts

- **`fetch_products.py`** — Fetches 40+ trending styles from 26 fashion RSS feeds, then gets real products from H&M via RapidAPI
- **`test_rss.py`** — Updates trending styles from RSS feeds
- **`curated_fits.py`** — Creates 10 hand-curated fits (5 men + 5 women) with color harmony
- **`quick_fetch.py`** — Quick scraper for testing (uses ScraperAPI)
- **`rebuild_products.py`** — Uses static ASOS CDN data (no API needed, for testing)

## Notes

- API keys should NEVER be hardcoded in source files
- Always use `.env` file with environment variables
- `.env` is in `.gitignore` and won't be committed to git
- Generated files (`products_data.js`, `products_data.json`) are ignored by git
