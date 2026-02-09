import json
import os
import time
from datetime import datetime
from listener import (
    INSTANCE_URL,
    HASHTAGS,
    fetch_tag_posts,
    strip_html,
    is_recent,
    is_spam,
    test_connection,
)

OUTPUT_FILE = "collected_posts.jsonl"

def save_post(record):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def get_saved_count():
    if not os.path.exists(OUTPUT_FILE):
        return 0
    count = 0
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            count = count + 1
    return count

def load_saved_ids():
    ids = set()
    if not os.path.exists(OUTPUT_FILE):
        return ids
    with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                ids.add(record["id"])
            except Exception:
                pass
    return ids

def run_saver():
    print("=" * 60)
    print("MASTODON DATA SAVER")
    print("=" * 60)
    print("Reading from:  Mastodon API (via listener.py)")
    print("Saving to:     " + OUTPUT_FILE)
    print("Hashtags:      " + str(len(HASHTAGS)))
    print("Polling every: 15 seconds")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    seen_ids = load_saved_ids()
    already_saved = len(seen_ids)
    print("Previously saved posts: " + str(already_saved))
    print("Resuming collection...\n")

    count = already_saved
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
                    tags.append(t["name"])

                record = {
                    "id": sid,
                    "created_at": created_at,
                    "collected_at": datetime.utcnow().isoformat() + "Z",
                    "author": author,
                    "author_followers": status["account"].get("followers_count", 0),
                    "content": content,
                    "language": language,
                    "tags": tags,
                    "reblogs_count": status.get("reblogs_count", 0),
                    "favourites_count": status.get("favourites_count", 0),
                    "replies_count": status.get("replies_count", 0),
                    "url": status.get("url", ""),
                }

                save_post(record)

                timestamp = datetime.now().strftime("%H:%M:%S")
                print("[" + timestamp + "] SAVED #" + str(count) + " | @" + author)
                print("  " + content[:150])
                print("  Tags: " + ", ".join(tags))

            time.sleep(0.3)

        timestamp = datetime.now().strftime("%H:%M:%S")
        file_size = 0
        if os.path.exists(OUTPUT_FILE):
            file_size = os.path.getsize(OUTPUT_FILE)
        size_kb = round(file_size / 1024, 1)
        print("[" + timestamp + "] Cycle " + str(cycle) + " | New: " + str(new_this_cycle) + " | Total: " + str(count) + " | Skipped: " + str(skipped) + " | File: " + str(size_kb) + " KB")
        print("")

        if len(seen_ids) > 50000:
            id_list = list(seen_ids)
            keep = id_list[-25000:]
            seen_ids = set(keep)

        time.sleep(15)

def main():
    print("Checking API connection...\n")
    if not test_connection():
        print("Cannot reach Mastodon API.")
        return
    run_saver()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        total = get_saved_count()
        file_size = 0
        if os.path.exists(OUTPUT_FILE):
            file_size = os.path.getsize(OUTPUT_FILE)
        size_kb = round(file_size / 1024, 1)
        print("\n")
        print("=" * 60)
        print("COLLECTION COMPLETE")
        print("=" * 60)
        print("Total posts saved: " + str(total))
        print("File: " + OUTPUT_FILE)
        print("Size: " + str(size_kb) + " KB")
        print("=" * 60)
