"""Persian text normalisation for search and alias matching."""
import re

_ARABIC_TO_PERSIAN = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "آ": "ا",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "‌": " ", "‏": "", "‎": "", "-": " ", "_": " ",
})
_DIACRITICS = re.compile(r"[ً-ٰٟـ]")
_SPACES = re.compile(r"\s+")


def normalize_fa(text: str) -> str:
    """Lower-case, unify Arabic/Persian letters & digits, drop ZWNJ and diacritics."""
    if not text:
        return ""
    text = _DIACRITICS.sub("", text.translate(_ARABIC_TO_PERSIAN)).lower()
    return _SPACES.sub(" ", text).strip()


def match_score(query: str, names: list[str]) -> int:
    """How well a normalised query matches an exercise's title/aliases (higher is better).

    Used to rank search results and, later, to map OCR'd gym slang
    ("زیربغل قایقی") to a canonical exercise.
    """
    best = 0
    for name in names:
        n = normalize_fa(name)
        if n == query:
            return 100
        if n.startswith(query):
            best = max(best, 70)
        elif query in n:
            best = max(best, 50)
        elif all(w in n for w in query.split()):
            best = max(best, 30)
    return best or 10
