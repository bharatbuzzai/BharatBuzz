import os

# --- RSS feeds (editable) ---
RSS_FEEDS = [
    "https://indianexpress.com/feed/",
    "https://www.thehindu.com/news/national/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvnews-top-stories?format=xml",
    "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml",
    "https://www.livemint.com/rss/news",
    "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
    "https://www.deccanherald.com/rss.xml",
    "https://www.indiatoday.in/rss/1206578",
    "https://www.news18.com/rss/india.xml",
    "https://economictimes.indiatimes.com/feeds/newsdefault.cms",
    "https://www.firstpost.com/feed/",
    "https://www.indiatvnews.com/rss/india.xml",
    "https://www.business-standard.com/rss/latest.rss",
    "https://www.financialexpress.com/feed/",
    "https://www.deccanchronicle.com/rss_feed",
    "https://www.newindianexpress.com/Nation/rssfeed/?id=170&getXmlFeed=true",
    "https://www.tribuneindia.com/rss/feed?catId=1",
    "https://www.dnaindia.com/feeds/india.xml",
    "https://www.oneindia.com/rss/oneindia-india-fb.xml",
    "https://www.bbc.com/news/world/asia/india/rss.xml",
]

# --- timing / thresholds ---
AGG_WINDOW_MINUTES = 90       # look for items in the last N minutes
MIN_SOURCES_FOR_TREND = 2     # need at least this many sources to call it multi-source trend
MAX_ARTICLES_TO_MERGE = 3     # how many full articles to fetch & merge
SUMMARY_WORDS = 120           # approx words in final summary for blog
BLOG_TITLE_MAX = 110

# --- output folders (docs/ is used so GitHub Pages can serve content) ---
DOCS_DIR = "docs"
IMAGES_DIR = os.path.join(DOCS_DIR, "images")

# Base URL for published blog pages (change via env or GitHub secret)
BLOG_BASE_URL = os.getenv("BLOG_BASE_URL", "https://bharatbuzzai.github.io/BharatBuzz")

# HTTP user agent
USER_AGENT = "Mozilla/5.0 (compatible; BharatBuzz/1.0; +https://github.com/bharatbuzzai/BharatBuzz)"
