from transformers import pipeline
from .logger import log
from .config import SUMMARY_WORDS
import math

_SUMM = None
_SUMM_MODEL = "sshleifer/distilbart-cnn-12-6"  # smaller distil model, free to use

def _get_summarizer():
    global _SUMM
    if _SUMM is None:
        try:
            log(f"Loading summarization model: {_SUMM_MODEL}")
            _SUMM = pipeline("summarization", model=_SUMM_MODEL)
            log("Summarization model loaded.")
        except Exception as e:
            log(f"⚠️ Could not load summarizer: {e}")
            _SUMM = None
    return _SUMM

def summarize(text: str, max_words: int = SUMMARY_WORDS):
    if not text:
        return ""
    # Coerce text length to something manageable
    text = text.strip()
    if len(text.split()) < 20:
        # short text -> return as-is
        return text

    summarizer = _get_summarizer()
    if summarizer is None:
        # fallback: naive two-sentence extract
        sents = text.split(".")
        return (". ".join(sents[:2])).strip() + ("..." if len(sents) > 2 else "")

    # Prepare max_length for the model (approx)
    max_len = min(220, int(max_words * 1.6))
    min_len = max(20, int(max_words * 0.4))

    try:
        # trim input a bit if extremely long
        trimmed = text[:8000]
        out = summarizer(trimmed, max_length=max_len, min_length=min_len, do_sample=False)
        return out[0]["summary_text"].strip()
    except Exception as e:
        log(f"Summarization error: {e}")
        # fallback
        sents = text.split(".")
        return (". ".join(sents[:2])).strip() + ("..." if len(sents) > 2 else "")
