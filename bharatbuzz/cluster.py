from datetime import datetime, timezone
from .config import MIN_SOURCES_FOR_TREND, MAX_ARTICLES_TO_MERGE
from .logger import log

def cluster_and_pick_trend(recent):
    if not recent:
        return None

    groups = {}
    for item in recent:
        key = item["norm"]
        groups.setdefault(key, []).append(item)

    best_key = None
    best_score = (-1, datetime.min.replace(tzinfo=timezone.utc))
    for k, items in groups.items():
        sources = set(i["source"] for i in items)
        latest = max(i["published"] for i in items)
        score = (len(sources), latest)
        if score > best_score:
            best_score = score
            best_key = k

    chosen = groups[best_key]
    distinct_sources = set(i["source"] for i in chosen)
    if len(distinct_sources) < MIN_SOURCES_FOR_TREND:
        log("No multi-source trend found; falling back to most recent single story.")
        chosen = [max(recent, key=lambda x: x["published"])]

    # dedupe
    uniq = []
    seen = set()
    for i in chosen:
        if i["link"] not in seen:
            uniq.append(i)
            seen.add(i["link"])
    return uniq[:MAX_ARTICLES_TO_MERGE]
