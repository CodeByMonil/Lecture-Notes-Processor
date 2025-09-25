import re

FILLERS = re.compile(r"\b(um|uh|er|ah|like|you know|kind of|sort of)\b", re.IGNORECASE)

def strip_fillers(text: str) -> str:
    # Gentle cleaner – removes common fillers when not inside words
    return FILLERS.sub("", text)

def squeeze_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
