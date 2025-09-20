# summarizer.py
import logging
from typing import List

# try to lazy-import transformers here so script still runs if model load fails
try:
    from transformers import pipeline
    SUMM_PIPE = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    logging.info("Loaded HuggingFace summarization model.")
except Exception as e:
    SUMM_PIPE = None
    logging.warning("Could not load HF summarizer model (fallback will be used). %s", e)


def fallback_headline(headlines: List[str]) -> str:
    # simple fallback: pick the most frequent tokens / or the longest headline if nothing else
    if not headlines:
        return ""
    # return the longest headline (as a safe fallback)
    return max(headlines, key=lambda s: len(s))[:240]


def summarize_headlines(headlines: List[str], max_words=25) -> str:
    """
    headlines: list of short headlines (strings)
    return: one-line summary (string)
    """
    if not headlines:
        return ""
    joined = " ||| ".join(headlines)
    if SUMM_PIPE:
        try:
            # request a short summary
            out = SUMM_PIPE(joined, max_length=max(30, int(max_words * 2.5)), min_length=5, do_sample=False)
            text = out[0]["summary_text"].replace("\n", " ").strip()
            # shorten to single line and safe size
            return text.split(".")[0][:240].strip()
        except Exception as e:
            # if the model fails, fallback
            return fallback_headline(headlines)
    else:
        return fallback_headline(headlines)
