# fetcher.py
import os
import re
import uuid
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from typing import List, Dict

# local folders
DOCS_DIR = "docs"
IMAGES_DIR = "images"

def ensure_dirs():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fetch_headlines(feeds: List[str], per_feed: int = 3) -> List[Dict]:
    """
    Returns a list of dicts: {title, link, feed_title, published}
    """
    items = []
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed)
            feed_title = parsed.feed.get("title", feed)
            for e in parsed.entries[:per_feed]:
                title = clean_text(e.get("title", "") or "")
                link = e.get("link", "") or ""
                if not title or not link:
                    continue
                # try to canonicalize pubdate
                dt = None
                try:
                    if hasattr(e, "published"):
                        dt = e.published
                    elif hasattr(e, "updated"):
                        dt = e.updated
                except Exception:
                    dt = None
                items.append({
                    "title": title,
                    "link": link,
                    "feed": feed_title,
                    "published": dt
                })
        except Exception:
            continue
    return items

def norm_title_simple(title: str) -> str:
    # quick normalization: lower, remove punctuation, keep long words
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    words = [w for w in t.split() if len(w) >= 4]
    # return sorted unique words as a stable key
    return " ".join(sorted(set(words))[:10])

def pick_best_cluster(items: List[Dict], min_sources=2):
    """
    Group by norm key; choose the cluster with most distinct sources; fallback to newest item.
    Returns list of items (cluster) or [].
    """
    groups = {}
    for it in items:
        key = norm_title_simple(it["title"])
        groups.setdefault(key, []).append(it)

    best_key = None
    best_score = (-1, None)
    for k, group in groups.items():
        sources = set([g["feed"] for g in group])
        # use len(sources) as primary score, fallback to latest published index
        score = (len(sources), len(group))
        if score > best_score:
            best_score = score
            best_key = k

    if not best_key:
        return []

    chosen = groups[best_key]
    if len(set([c["feed"] for c in chosen])) < min_sources:
        # no cross-source cluster found -> fallback to most recent single item
        return [max(items, key=lambda x: x.get("published") or "")]

    # deduplicate by link
    uniq = []
    seen = set()
    for i in chosen:
        if i["link"] not in seen:
            uniq.append(i)
            seen.add(i["link"])
    return uniq

def fetch_article_image(url: str) -> str:
    """Return image URL from article's meta tags or empty string"""
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in (("meta", {"property": "og:image"}), ("meta", {"name": "og:image"}),
                    ("meta", {"property": "twitter:image"}), ("meta", {"name": "twitter:image"})):
            el = soup.find(tag[0], attrs=tag[1])
            if el:
                content = el.get("content") or el.get("value") or ""
                if content:
                    return content.strip()
        # fallback: find first <img> inside article/main sections
        for sel in ["article img", "main img", "section img", "div img"]:
            img = soup.select_one(sel)
            if img and img.get("src"):
                return img["src"]
    except Exception:
        pass
    return ""

def download_image_to_images(url: str, slug_seed: str = None) -> str:
    """
    Downloads image and stores under images/<slug>.jpg
    Returns local path (images/foo.jpg) or empty string on failure.
    """
    if not url:
        return ""
    try:
        # try to complete relative urls
        if url.startswith("//"):
            url = "https:" + url
        if not url.startswith("http"):
            return ""
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return ""
        ext = ".jpg"
        slug = (slug_seed or "img") + "-" + uuid.uuid4().hex[:6]
        path = os.path.join(IMAGES_DIR, slug + ext)
        with open(path, "wb") as f:
            f.write(r.content)
        return path
    except Exception:
        return ""
