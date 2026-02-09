import requests
import json
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
import time
import re

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

INSTANCE_URL = "https://mastodon.social"

HASHTAGS = [
    "mentalhealth",
    "depression",
    "anxiety",
    "depressed",
    "anxious",
    "panic",
    "stressed",
    "stress",
    "burnout",
    "loneliness",
    "lonely",
    "ptsd",
    "trauma",
    "therapy",
    "overwhelmed",
    "insomnia",
    "selfcare",
    "mentalhealthawareness",
    "struggling",
]

SKIP_AUTHORS = [
    "lisawarnerlisaluv",
]

MIN_CONTENT_LENGTH = 30
MAX_EMOJI_RATIO = 0.5
MAX_AGE_HOURS = 24

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
    emoji_count = 0
    for char in content:
        if ord(char) > 127:
            emoji_count = emoji_count + 1
    total = len(content)
    if total > 0 and emoji_count / total > MAX_EMOJI_RATIO:
        return True
    upper_count = 0
    alpha_count = 0
    for char in content:
        if char.isalpha():
            alpha_count = alpha_count + 1
            if char.isupper():
                upper_count = upper_count + 1
    if alpha_count > 20 and upper_count / alpha_count > 0.7:
        return True
    return False

def fetch_tag_posts(tag):
    url = INSTANCE_URL + "/api/v1/timelines/tag/" + tag
    try:
        resp = requests.get(url, params={"limit": 20}, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return []
    except Exception as e:
        print("Error fetching #" + tag + ": " + str(e))
        return []

def test_connection():
    print("Testing API connection...")
    url = INSTANCE_URL + "/api/v1/timelines/tag/mentalhealth"
    try:
        resp = requests.get(url, params={"limit": 3}, timeout=10)
        print("  Status code: " + str(resp.status_code))
        if resp.status_code == 200:
            posts = resp.json()
            print("  Got " + str(len(posts)) + " posts from #mentalhealth")
            print("  API is reachable!\n")
            return True
        else:
            print("  Error")
            return False
    except Exception as e:
        print("  Failed: " + str(e))
        return False

def poll_mode():
    print("=" * 60)
    print("MASTODON MENTAL HEALTH LISTENER")
    print("=" * 60)
    print("Monitoring " + str(len(HASHTAGS)) + " hashtags")
    print("Filters:")
    print("  - Only posts from last " + str(MAX_AGE_HOURS) + " hours")
    print("  - Skip spam/emoji-heavy posts")
    print("  - Skip known spam accounts")
    print("  - Minimum " + str(MIN_CONTENT_LENGTH) + " chars of real content")
    print("Polling every 15 seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    seen_ids = set()
    count = 0
    skipped = 0
    cycle = 0

    while True:
        cycle = cycle + 1
        new_this_cycle = 0

        for tag in HASHTAGS:
            posts = fetch_tag_posts(tag)
            for status in posts:
                sid = status["id"]
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)

                created_at = status.get("created_at", "")
                if not is_recent(created_at):
                    skipped = skipped + 1
                    continue

                author = status["account"]["acct"]
                content = strip_html(status["content"])

                if is_spam(content, author):
                    skipped = skipped + 1
                    continue

                language = status.get("language", "?")
                if language not in ["en", "?", None]:
                    skipped = skipped + 1
                    continue

                count = count + 1
                new_this_cycle = new_this_cycle + 1

                tag_list = status.get("tags", [])
                tags = []
                for t in tag_list:
                    tags.append("#" + t["name"])

                reblogs = status.get("reblogs_count", 0)
                favs = status.get("favourites_count", 0)
                replies = status.get("replies_count", 0)

                timestamp = datetime.now().strftime("%H:%M:%S")
                print("[" + timestamp + "] POST #" + str(count))
                print("  Author:   @" + author)
                print("  Created:  " + str(created_at))
                print("  Content:  " + content[:400])
                print("  Tags:     " + " ".join(tags))
                print("  Boosts: " + str(reblogs) + " | Favs: " + str(favs) + " | Replies: " + str(replies))
                print("  URL:      " + status.get("url", "N/A"))
                print("-" * 60)

            time.sleep(0.3)

        timestamp = datetime.now().strftime("%H:%M:%S")
        print("[" + timestamp + "] Cycle " + str(cycle) + " done | New: " + str(new_this_cycle) + " | Total: " + str(count) + " | Skipped: " + str(skipped))

        if len(seen_ids) > 50000:
            id_list = list(seen_ids)
            keep = id_list[-25000:]
            seen_ids = set(keep)

        time.sleep(15)

def main():
    if not test_connection():
        print("Cannot reach Mastodon API.")
        return
    poll_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nStopped listening.")
        print("Done!")
