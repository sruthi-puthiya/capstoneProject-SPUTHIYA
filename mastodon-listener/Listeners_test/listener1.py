import requests
import json
import re
from datetime import datetime
from html.parser import HTMLParser
import time

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
ACCESS_TOKEN = "Yx8tVFSq93kkbJKY1Wz2vkmZhVN4sa-LWSjVC-5uXo8"

KEYWORDS = [
    "depressed",
    "depression",
    "anxious",
    "anxiety",
    "panic",
    "angry",
    "anger",
    "hopeless",
    "helpless",
    "stressed",
    "stress",
    "lonely",
    "loneliness",
    "suicidal",
    "self harm",
    "mental health",
    "overwhelmed",
    "burnout",
    "insomnia",
    "cant sleep",
    "can't sleep",
    "feeling down",
    "feeling sad",
    "feel lost",
    "hate myself",
    "worthless",
    "crying",
    "breakdown",
    "trauma",
    "ptsd",
    "therapy",
    "therapist",
    "exhausted",
    "emotional",
    "struggling",
    "suffer",
    "suffering",
    "miserable",
    "sad",
    "scared",
    "afraid",
    "worried",
    "worry",
    "fearful",
    "frustrated",
    "rage",
    "despair",
    "numb",
    "empty inside",
]

def get_headers():
    return {"Authorization": "Bearer " + ACCESS_TOKEN}

def matches_keywords(text):
    text_lower = text.lower()
    matched = []
    for kw in KEYWORDS:
        if kw in text_lower:
            matched.append(kw)
    return matched

def test_connection():
    print("Testing API connection...")
    try:
        resp = requests.get(
            INSTANCE_URL + "/api/v1/timelines/public",
            headers=get_headers(),
            params={"limit": 5},
            timeout=10
        )
        print("  Status code: " + str(resp.status_code))
        if resp.status_code == 200:
            posts = resp.json()
            print("  Got " + str(len(posts)) + " posts from API")
            for p in posts:
                author = p["account"]["acct"]
                content = strip_html(p["content"])
                print("  @" + author + ": " + content[:80])
            print("\n  API is reachable!\n")
            return True
        else:
            print("  Error: " + resp.text)
            return False
    except Exception as e:
        print("  Connection failed: " + str(e))
        return False

def poll_mode():
    print("=" * 60)
    print("MASTODON MENTAL HEALTH KEYWORD LISTENER")
    print("=" * 60)
    print("Monitoring keywords: " + ", ".join(KEYWORDS[:10]) + "...")
    print("Polling every 5 seconds...")
    print("Press Ctrl+C to stop\n")

    seen_ids = set()
    count = 0
    total_scanned = 0

    while True:
        try:
            resp = requests.get(
                INSTANCE_URL + "/api/v1/timelines/public",
                headers=get_headers(),
                params={"limit": 40},
                timeout=10
            )
            if resp.status_code == 200:
                posts = resp.json()
                for status in posts:
                    sid = status["id"]
                    if sid not in seen_ids:
                        seen_ids.add(sid)
                        total_scanned = total_scanned + 1
                        content = strip_html(status["content"])
                        if not content:
                            continue
                        matched = matches_keywords(content)
                        if len(matched) > 0:
                            count = count + 1
                            author = status["account"]["acct"]
                            language = status.get("language", "?")
                            tag_list = status.get("tags", [])
                            tags = []
                            for t in tag_list:
                                tags.append(t["name"])
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            print("[" + timestamp + "] MATCH #" + str(count) + " (scanned: " + str(total_scanned) + ")")
                            print("  Author: @" + author + " (" + language + ")")
                            print("  Keywords: " + ", ".join(matched))
                            print("  Content: " + content[:300])
                            if len(tags) > 0:
                                print("  Tags: " + ", ".join(tags))
                            print("  URL: " + status.get("url", "N/A"))
                            print("=" * 60)
                if total_scanned % 100 == 0 and total_scanned > 0:
                    print("... scanned " + str(total_scanned) + " posts, found " + str(count) + " matches ...")
            else:
                print("API returned: " + str(resp.status_code))
            if len(seen_ids) > 50000:
                seen_ids = set(list(seen_ids)[-25000:])
            time.sleep(5)
        except Exception as e:
            print("Request error: " + str(e))
            time.sleep(10)

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
