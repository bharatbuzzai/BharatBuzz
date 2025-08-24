import os
import sys
import traceback
from datetime import datetime

DEBUG = os.getenv("BB_DEBUG", "1") == "1"

def log(msg: str):
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts} UTC] {msg}")

def log_section(title: str):
    line = "=" * 60
    log(f"{line}\n{title}\n{line}")

def log_error(stage: str, err: Exception):
    etype = type(err).__name__
    log(f"❌ ERROR in {stage}: {etype}: {err}")
    if DEBUG:
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
        print(tb, file=sys.stderr)
