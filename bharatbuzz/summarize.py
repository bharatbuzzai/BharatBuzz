from transformers import pipeline
from .config import SUMMARY_WORDS
from .logger import log, log_error

# Load once (cached across steps)
try:
    SUMM = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    log("Loaded summarization model: sshleifer/distilbart-cnn-12-6")
except Exception as e:
    SUMM = None

def summarize(text: str, max_words=SUMMARY_WORDS):
    if not text:
        return ""
    if not SUMM:
        log("WARN: Summarizer not available, returning raw text (truncated).")
        return text[:1200]
    try:
        max_len = max(60, min(220, int(max_words * 1.3)))
        result = SUMM(text, max_length=max_len, min_length=80, do_sample=False)
        return result[0]["summary_text"]
    except Exception as e:
        log_error("Summarize", e)
        return text[:1200]
