import os
import re
import uuid
from datetime import datetime
from .config import DOCS_DIR, IMAGES_DIR, BLOG_TITLE_MAX
from .logger import log

def ensure_dirs():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)

def build_slug(title: str):
    t = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip())[:80].strip("-")
    return t + "-" + uuid.uuid4().hex[:6]

def pick_hashtags(title: str):
    words = re.findall(r"[A-Za-z]{4,}", title)
    base = ["#BharatBuzzAI", "#IndiaNews"]
    for w in words[:2]:
        base.append(f"#{w.title()}")
    return " ".join(base)

def write_markdown(slug: str, title: str, summary: str, image_rel: str, sources: list):
    path = os.path.join(DOCS_DIR, f"{slug}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"*Published:* {datetime.now().strftime('%d %B %Y, %H:%M')}\n\n")
        if image_rel:
            f.write(f"![cover]({image_rel})\n\n")
        f.write(summary.strip() + "\n\n")
        f.write("**Sources:**\n")
        for s in sources:
            f.write(f"- [{s['source']}]({s['link']})\n")
    log(f"Wrote blog: {path}")
    return path
