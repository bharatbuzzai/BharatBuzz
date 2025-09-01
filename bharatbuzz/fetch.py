import feedparser
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from dateutil import parser as dateparser
from .logger import log
from .config import USER_AGENT, IMAGES_DIR

import os
from PIL import Image
import io

def parse_pubdate(entry):
    # entry may be dict-like; try common fields
    for key in ("published", "updated", "pubDate", "dc:date"):
        val = entry.get(key) if isinstance(entry, dict) else entry.get(key, None)
        if val:
            try:
                return dateparser.parse(val)
            except Exception:
                pass
    # try published_parsed
    pp = entry.get("published_parsed") or entry.get("updated_parsed")
    if pp:
        try:
            return datetime(*pp[:6], tzinfo=timezone.utc)
        except Exception:
            pass
    return None

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def fetch_recent_entries(feeds, window_minutes=90, per_feed=6):
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)
    results = []
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed)
            if parsed.bozo:
                log(f"⚠️ Feed parse problem (skipping): {feed}")
            for e in (parsed.entries or [])[:per_feed]:
                title = clean_text(e.get("title", "") or "")
                link = e.get("link", "") or ""
                if not title or not link:
                    continue
                dt = parse_pubdate(e) or None
                if not dt:
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if dt < cutoff:
                    continue
                results.append({
                    "title": title,
                    "link": link,
                    "source": parsed.feed.get("title", feed),
                    "published": dt
                })
        except Exception as ex:
            log(f"RSS error for {feed}: {ex}")
    # sort newest first
    results.sort(key=lambda x: x["published"], reverse=True)
    return results

def fetch_article_text_and_image(url, timeout=12):
    headers = {"User-Agent": USER_AGENT}
    try:
        r = requests.get(url, timeout=timeout, headers=headers)
        if r.status_code != 200:
            return "", None
        soup = BeautifulSoup(r.text, "html.parser")

        # find og:image or twitter:image
        img_url = None
        for prop in ("og:image", "twitter:image"):
            tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                img_url = tag["content"].strip()
                break

        # try article container
        text_blocks = []
        selectors = ["article", "div[itemprop='articleBody']", "div[class*='article']", "div[class*='content']", "section", "main"]
        for sel in selectors:
            cont = soup.select_one(sel)
            if cont:
                ps = cont.find_all("p")
                if len(ps) >= 3:
                    text_blocks = [p.get_text(" ", strip=True) for p in ps]
                    break

        if not text_blocks:
            ps = soup.find_all("p")
            text_blocks = [p.get_text(" ", strip=True) for p in ps[:12]]

        full_text = clean_text(" ".join(text_blocks))
        return full_text, img_url
    except Exception as e:
        log(f"fetch_article_text_and_image error for {url}: {e}")
        return "", None

def download_image(url: str, slug: str, images_dir=IMAGES_DIR):
    if not url:
        return None
    try:
        os.makedirs(images_dir, exist_ok=True)
        r = requests.get(url, timeout=12, headers={"User-Agent": USER_AGENT})
        if r.status_code != 200:
            return None
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        fname = f"{slug}.jpg"
        path = os.path.join(images_dir, fname)
        im.save(path, format="JPEG", quality=85)
        return path
    except Exception as e:
        log(f"download_image failed: {e}")
        return None

# local import for timedelta
from datetime import timedelta
