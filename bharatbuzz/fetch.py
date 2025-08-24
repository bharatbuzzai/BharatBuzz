import os
import re
import io
import html
import requests
import feedparser
from PIL import Image
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser

from .logger import log, log_error
from .config import AGG_WINDOW_MINUTES, IMAGES_DIR
from .feeds import RSS_FEEDS

STOPWORDS = set("""
a an the of for on in and or at to with from by about into over under across up down off out as is be will would could should
this that these those here there where when how why which who whom whose are were been being have has had do does did not
""".split())

def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)

def clean_text(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = BeautifulSoup(s, "html.parser").get_text(" ", strip=True)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_pubdate(e):
    dt = None
    for k in ["published", "updated", "pubDate", "dc:date"]:
        if getattr(e, k, None):
            try:
                dt = dateparser.parse(getattr(e, k))
                break
            except Exception:
                pass
    if not dt:
        pp = getattr(e, "published_parsed", None) or getattr(e, "updated_parsed", None)
        if pp:
            try:
                dt = datetime(*pp[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return dt

def norm_title(title: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    words = [w for w in t.split() if len(w) >= 4 and w not in STOPWORDS]
    words = sorted(set(words))
    return " ".join(words[:10])

def fetch_recent_entries():
    log("Fetching RSS entries within window...")
    recent = []
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=AGG_WINDOW_MINUTES)

    for feed in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed)
            for e in parsed.entries[:6]:
                title = clean_text(getattr(e, "title", ""))
                link  = getattr(e, "link", "")
                if not title or not link:
                    continue
                dt = parse_pubdate(e)
                if dt and dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                if not dt or dt < cutoff:
                    continue
                recent.append({
                    "title": title,
                    "link": link,
                    "source": parsed.feed.get("title", feed),
                    "published": dt,
                    "norm": norm_title(title),
                })
        except Exception as ex:
            log_error("RSS parse", ex)
    log(f"Collected {len(recent)} recent items.")
    return recent

def fetch_article_text_and_image(url: str):
    try:
        r = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code != 200:
            return "", None
        soup = BeautifulSoup(r.text, "html.parser")
        img_url = None
        for prop in ["og:image", "twitter:image"]:
            tag = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
            if tag and tag.get("content"):
                img_url = tag["content"].strip()
                break

        text_blocks = []
        for sel in ["article", "div[itemprop='articleBody']", "div[class*='article']",
                    "div[class*='content']", "section", "main"]:
            cont = soup.select_one(sel)
            if cont:
                ps = cont.find_all("p")
                if len(ps) > 3:
                    text_blocks = [p.get_text(" ", strip=True) for p in ps]
                    break
        if not text_blocks:
            ps = soup.find_all("p")
            text_blocks = [p.get_text(" ", strip=True) for p in ps[:12]]
        full_text = clean_text(" ".join(text_blocks))
        return full_text, img_url
    except Exception as e:
        log_error("Fetch article", e)
        return "", None

def download_image(url: str, out_path: str):
    if not url:
        return False
    try:
        r = requests.get(url, timeout=12)
        if r.status_code != 200:
            return False
        im = Image.open(io.BytesIO(r.content)).convert("RGB")
        im.save(out_path, format="JPEG", quality=88)
        return True
    except Exception as e:
        log_error("Download image", e)
        return False
