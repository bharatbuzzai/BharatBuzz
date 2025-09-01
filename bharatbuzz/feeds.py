from .config import RSS_FEEDS

def get_feeds():
    # Single function so future changes (DB, remote list) are easy
    return RSS_FEEDS
