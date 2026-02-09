# producer.py

import json
import time
import requests
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

from config import (
    INSTANCE_URL,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_RAW,
    HASHTAGS,
    POLL_INTERVAL_SECONDS,
    FETCH_LIMIT_PER_TAG,
)
from utils import strip_html, is_recent, is_spam


def create_producer(retries=5, delay=5):
    """Create Kafka producer with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
                max_in_flight_requests_per_connection=1,
                linger_ms=10,
                batch_size=16384,
            )
            print("Kafka producer connected.")
            return producer
        except NoBrokersAvailable:
            print(
                f"  Attempt {attempt}/{retries} — no brokers available, "
                f"retrying in {delay}s..."
            )
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after multiple attempts.")


def test_mastodon_connection():
    """Verify the Mastodon API is reachable."""
    print("Testing Mastodon API connection...")
    url = f"{INSTANCE_URL}/api/v1/timelines/tag/mentalhealth"
    try:
        resp = requests.get(url, params={"limit": 3}, timeout=10)
        print(f"  Status code: {resp.status_code}")
        if resp.status_code == 200:
            posts = resp.json()
            print(f"  Got {len(posts)} posts from #mentalhealth")
            print("  API is reachable!\n")
            return True
        return False
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def fetch_tag_posts(tag):
    """Fetch recent posts for a given hashtag."""
    url = f"{INSTANCE_URL}/api/v1/timelines/tag/{tag}"
    try:
        resp = requests.get(
            url, params={"limit": FETCH_LIMIT_PER_TAG}, timeout=10
        )
        if resp.status_code == 200:
            return resp.json()
        return []
    except Exception as e:
        print(f"Error fetching #{tag}: {e}")
        return []


def build_message(status, matched_tag):
    """
    Transform a raw Mastodon status into a clean message dict
    suitable for Kafka.
    """
    tag_list = [f"#{t['name']}" for t in status.get("tags", [])]
    content_plain = strip_html(status.get("content", ""))

    return {
        "id": status["id"],
        "created_at": status.get("created_at", ""),
        "author": status["account"]["acct"],
        "author_display_name": status["account"].get("display_name", ""),
        "author_followers": status["account"].get("followers_count", 0),
        "content_html": status.get("content", ""),
        "content_plain": content_plain,
        "language": status.get("language"),
        "tags": tag_list,
        "matched_tag": matched_tag,
        "url": status.get("url", ""),
        "reblogs_count": status.get("reblogs_count", 0),
        "favourites_count": status.get("favourites_count", 0),
        "replies_count": status.get("replies_count", 0),
        "sensitive": status.get("sensitive", False),
        "visibility": status.get("visibility", "public"),
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }


def run_producer():
    """Main producer loop: poll Mastodon, filter, publish to Kafka."""
    if not test_mastodon_connection():
        print("Cannot reach Mastodon API. Exiting.")
        return

    producer = create_producer()

    print("=" * 60)
    print("MASTODON → KAFKA PRODUCER")
    print("=" * 60)
    print(f"Monitoring {len(HASHTAGS)} hashtags")
    print(f"Publishing to topic: {KAFKA_TOPIC_RAW}")
    print(f"Polling every {POLL_INTERVAL_SECONDS}s")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    seen_ids = set()
    total_published = 0
    total_skipped = 0
    cycle = 0

    while True:
        cycle += 1
        new_this_cycle = 0

        for tag in HASHTAGS:
            posts = fetch_tag_posts(tag)

            for status in posts:
                sid = status["id"]
                if sid in seen_ids:
                    continue
                seen_ids.add(sid)

                # ---- Pre-filter before publishing ----
                created_at = status.get("created_at", "")
                if not is_recent(created_at):
                    total_skipped += 1
                    continue

                author = status["account"]["acct"]
                content = strip_html(status.get("content", ""))

                if is_spam(content, author):
                    total_skipped += 1
                    continue

                language = status.get("language", "?")
                if language not in ("en", "?", None):
                    total_skipped += 1
                    continue

                # ---- Build and publish ----
                message = build_message(status, matched_tag=tag)

                producer.send(
                    KAFKA_TOPIC_RAW,
                    key=sid,
                    value=message,
                )
                total_published += 1
                new_this_cycle += 1

                ts = datetime.now().strftime("%H:%M:%S")
                print(
                    f"[{ts}] Published #{total_published} | "
                    f"@{author} | #{tag} | "
                    f"{content[:80]}..."
                )

            time.sleep(0.3)  # polite rate-limiting between tags

        producer.flush()

        ts = datetime.now().strftime("%H:%M:%S")
        print(
            f"[{ts}] Cycle {cycle} done | "
            f"New: {new_this_cycle} | "
            f"Total: {total_published} | "
            f"Skipped: {total_skipped}"
        )

        # Prevent unbounded memory growth
        if len(seen_ids) > 50_000:
            seen_ids = set(list(seen_ids)[-25_000:])

        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        run_producer()
    except KeyboardInterrupt:
        print("\n\nProducer stopped.")
