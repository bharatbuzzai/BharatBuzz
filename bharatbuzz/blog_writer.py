import os
from datetime import datetime
from .logger import log
from .config import DOCS_DIR

def build_slug(title: str) -> str:
    import re, uuid
    t = re.sub(r"[^a-zA-Z0-9]+", "-", title.strip())[:80].strip("-")
    return f"{t}-{uuid.uuid4().hex[:6]}"

def save_blog(title: str, summary: str, stories: list, image_path: str = None, slug: str = None):
    os.makedirs(DOCS_DIR, exist_ok=True)
    if not slug:
        slug = build_slug(title)
    filename = os.path.join(DOCS_DIR, f"{slug}.md")

    lines = []
    lines.append(f"# {title}\n")
    lines.append(f"*Published:* {datetime.utcnow().strftime('%d %B %Y, %H:%M UTC')}\n")

    if image_path:
        # image stored *inside* docs/images — saved by fetch download
        rel_img = f"images/{os.path.basename(image_path)}"
        lines.append(f"![cover]({rel_img})\n")

    lines.append(summary + "\n\n")
    lines.append("**Sources:**\n")
    for s in stories:
        lines.append(f"- [{s['source']}]({s['link']})")
    content = "\n".join(lines) + "\n"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    log(f"Wrote blog: {filename}")
    return filename
