# utils.py

from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from config import (
    MIN_CONTENT_LENGTH,
    MAX_EMOJI_RATIO,
    MAX_AGE_HOURS,
    SKIP_AUTHORS,
)


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []

    def handle_data(self, d):
        self.result.append(d)

    def get_text(self):
        return "".join(self.result)


def strip_html(html):
    if not html:
        return ""
    s = HTMLStripper()
    s.feed(html)
    return s.get_text()


def is_recent(created_at_str):
    try:
        created_at_str = created_at_str.replace("Z", "+00:00")
        created = datetime.fromisoformat(created_at_str)
        now = datetime.now(timezone.utc)
        age = now - created
        return age < timedelta(hours=MAX_AGE_HOURS)
    except Exception:
        return True


def is_spam(content, author):
    if author.lower() in SKIP_AUTHORS:
        return True
    if len(content) < MIN_CONTENT_LENGTH:
        return True

    emoji_count = sum(1 for char in content if ord(char) > 127)
    total = len(content)
    if total > 0 and emoji_count / total > MAX_EMOJI_RATIO:
        return True

    upper_count = 0
    alpha_count = 0
    for char in content:
        if char.isalpha():
            alpha_count += 1
            if char.isupper():
                upper_count += 1
    if alpha_count > 20 and upper_count / alpha_count > 0.7:
        return True

    return False
