import requests
import json
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
    "selfharm",
    "suicideprevention",
    "ptsd",
    "trauma",
    "therapy",
    "overwhelmed",
    "insomnia",
    "selfcare",
    "mentalhealthawareness",
    "sad",
    "angry",
    "hopeless",
    "struggling",
]

def fetch_tag_posts(tag):
    url = INSTANCE_URL + "/api/v1/timelines/tag/" + tag
    try:
        resp = requests.get(url, params={"limit": 40}, timeout=10)
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
            for p in posts:
                author = p["account"]["acct"]
                content = strip_html(p["content"])
                print("  @" + author + ": " + content[:80])
            print("\n  API is reachable!\n")
            return True
        else:
            print("  Error response")
            return False
    except Exception as e:
        print("  Failed: " + str(e))
        return False

def poll_mode():
    print("=" * 60)
    print("MASTODON MENTAL HEALTH LISTENER")
    print("=" * 60)
    print("Monitoring " + str(len(HASHTAGS)) + " hashtags:")
    for h in HASHTAGS:
        print("  #" + h)
    print("")
    print("Polling every 10 seconds...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    seen_ids = set()
    count = 0
    cycle = 0

    while True:
        cycle = cycle + 1
        new_this_cycle = 0

        for tag in HASHTAGS:
            posts = fetch_tag_posts(tag)
            for status in posts:
                sid = status["id"]
                if sid not in seen_ids:
                    seen_ids.add(sid)
                    count = count + 1
                    new_this_cycle = new_this_cycle + 1

                    author = status["account"]["acct"]
                    content = strip_html(status["content"])
                    language = status.get("language", "?")
                    created = status.get("created_at", "?")
                    url = status.get("url", "N/A")

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
                    print("  Language: " + str(language))
                    print("  Created:  " + str(created))
                    print("  Content:  " + content[:300])
                    print("  Tags:     " + " ".join(tags))
                    print("  Boosts: " + str(reblogs) + " | Favs: " + str(favs) + " | Replies: " + str(replies))
                    print("  URL:      " + url)
                    print("-" * 60)

            time.sleep(0.5)

        if new_this_cycle == 0:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print("[" + timestamp + "] Cycle " + str(cycle) + " - no new posts (total: " + str(count) + ", seen: " + str(len(seen_ids)) + ")")

        if len(seen_ids) > 50000:
            old_size = len(seen_ids)
            id_list = list(seen_ids)
            keep = id_list[-25000:]
            seen_ids = set(keep)
            print("Cleaned seen_ids: " + str(old_size) + " -> " + str(len(seen_ids)))

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
