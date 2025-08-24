import os

# RSS aggregation window
AGG_WINDOW_MINUTES = int(os.getenv("BB_WINDOW_MINUTES", "90"))
MIN_SOURCES_FOR_TREND = int(os.getenv("BB_MIN_SOURCES", "2"))
MAX_ARTICLES_TO_MERGE = int(os.getenv("BB_MAX_ARTICLES", "3"))
SUMMARY_WORDS = int(os.getenv("BB_SUMMARY_WORDS", "160"))
BLOG_TITLE_MAX = int(os.getenv("BB_TITLE_MAX", "110"))

DOCS_DIR = "docs"
IMAGES_DIR = "images"

# Pages base URL, e.g., https://bharatbuzzai.github.io/BharatBuzz
BLOG_BASE_URL = os.getenv("BLOG_BASE_URL", "")

# Twitter credentials
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET", "")
