import re
from .logger import log
from .config import MIN_SOURCES_FOR_TREND, MAX_ARTICLES_TO_MERGE
from collections import defaultdict
from datetime import datetime, timezone

STOPWORDS = set("""a an the of for on in and or at to with from by about into over under across up down off out as is be will would could should this that these those here there where when how why which who whom whose are were been being have has had do does did not""".split())

def norm_title(title: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower())
    tokens = [w for w in t.split() if len(w) >= 4 and w not in STOPWORDS]
    tokens = sorted(set(tokens))
    return " ".join(tokens[:10])

def cluster_and_pick_trend(recent):
    if not recent:
        return None
    groups = defaultdict(list)
    for item in recent:
        key = norm_title(item["title"])
        groups[key].append(item)

    # choose best group: by distinct source count, then latest time
    best_key = None
    best_score = (-1, datetime.min.replace(tzinfo=timezone.utc))
    for k, items in groups.items():
        srcs = set(i["source"] for i in items)
        latest = max(i["published"] for i in items)
        score = (len(srcs), latest)
        if score > best_score:
            best_score = score
            best_key = k

    chosen = groups[best_key]
    distinct_sources = set(i["source"] for i in chosen)
    if len(distinct_sources) < MIN_SOURCES_FOR_TREND:
        log("No multi-source trend found; falling back to the freshest story.")
        # fallback: single freshest article
        freshest = max(recent, key=lambda x: x["published"])
        return [freshest]

    # deduplicate by link and limit
    uniq = []
    seen = set()
    for i in chosen:
        if i["link"] not in seen:
            uniq.append(i)
            seen.add(i["link"])
    return uniq[:MAX_ARTICLES_TO_MERGE]
