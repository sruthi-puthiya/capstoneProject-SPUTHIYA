# consumer.py

import json
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable
import time

from config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC_RAW,
    KAFKA_CONSUMER_GROUP,
)


# ---------------------------------------------------------------------------
# Keyword-based distress scoring (lightweight — swap for ML later)
# ---------------------------------------------------------------------------
DISTRESS_KEYWORDS = {
    "high": [
        "suicid", "kill myself", "end my life", "want to die",
        "don't want to live", "self harm", "cutting myself",
        "no reason to live", "hopeless",
    ],
    "medium": [
        "depressed", "can't cope", "breaking down", "panic attack",
        "can't breathe", "crying", "numb", "worthless",
        "nobody cares", "all alone", "give up", "exhausted",
        "can't sleep", "overwhelmed", "falling apart",
    ],
    "low": [
        "stressed", "anxious", "worried", "struggling",
        "tough day", "bad day", "burned out", "burnout",
        "tired", "frustrated", "sad", "lonely",
    ],
}


def score_distress(content):
    """Return (level, matched_keywords) for a piece of text."""
    lower = content.lower()
    for level in ("high", "medium", "low"):
        matched = [kw for kw in DISTRESS_KEYWORDS[level] if kw in lower]
        if matched:
            return level, matched
    return "none", []


def create_consumer(retries=5, delay=5):
    """Create Kafka consumer with retry logic."""
    for attempt in range(1, retries + 1):
        try:
            consumer = KafkaConsumer(
                KAFKA_TOPIC_RAW,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=KAFKA_CONSUMER_GROUP,
                auto_offset_reset="latest",       # or "earliest" to replay
                enable_auto_commit=True,
                auto_commit_interval_ms=5000,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                key_deserializer=lambda k: k.decode("utf-8") if k else None,
                consumer_timeout_ms=-1,            # block forever
            )
            print("Kafka consumer connected.")
            return consumer
        except NoBrokersAvailable:
            print(
                f"  Attempt {attempt}/{retries} — no brokers, "
                f"retrying in {delay}s..."
            )
            time.sleep(delay)
    raise RuntimeError("Could not connect to Kafka after multiple attempts.")


def format_post(msg, count, distress_level, distress_keywords):
    """Pretty-print a consumed post."""
    ts = datetime.now().strftime("%H:%M:%S")

    level_icon = {
        "high": "🔴 HIGH",
        "medium": "🟡 MEDIUM",
        "low": "🟢 LOW",
        "none": "⚪ NONE",
    }

    lines = [
        f"[{ts}] POST #{count}  |  Distress: {level_icon.get(distress_level, distress_level)}",
        f"  Author:    @{msg['author']}",
        f"  Created:   {msg['created_at']}",
        f"  Content:   {msg['content_plain'][:400]}",
        f"  Tags:      {' '.join(msg.get('tags', []))}",
        f"  Matched:   #{msg.get('matched_tag', '')}",
        f"  Boosts: {msg.get('reblogs_count', 0)} | "
        f"Favs: {msg.get('favourites_count', 0)} | "
        f"Replies: {msg.get('replies_count', 0)}",
        f"  URL:       {msg.get('url', 'N/A')}",
    ]
    if distress_keywords:
        lines.append(f"  Keywords:  {', '.join(distress_keywords)}")
    lines.append("-" * 60)
    return "\n".join(lines)


def run_consumer():
    """Main consumer loop: read from Kafka, score, display."""
    consumer = create_consumer()

    print("=" * 60)
    print("KAFKA MENTAL HEALTH CONSUMER")
    print("=" * 60)
    print(f"Topic:          {KAFKA_TOPIC_RAW}")
    print(f"Consumer group: {KAFKA_CONSUMER_GROUP}")
    print("Waiting for messages...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    count = 0
    high_count = 0
    medium_count = 0

    for record in consumer:
        msg = record.value
        count += 1

        distress_level, distress_keywords = score_distress(
            msg.get("content_plain", "")
        )

        if distress_level == "high":
            high_count += 1
        elif distress_level == "medium":
            medium_count += 1

        output = format_post(msg, count, distress_level, distress_keywords)
        print(output)

        # ---- HIGH-distress alert example ----
        if distress_level == "high":
            print("  ⚠️  HIGH DISTRESS DETECTED — would trigger alert/webhook")
            print("-" * 60)

        # Periodic summary
        if count % 25 == 0:
            print(f"\n{'='*60}")
            print(f"  SUMMARY after {count} posts")
            print(f"  High distress:   {high_count}")
            print(f"  Medium distress: {medium_count}")
            print(f"{'='*60}\n")


if __name__ == "__main__":
    try:
        run_consumer()
    except KeyboardInterrupt:
        print(f"\n\nConsumer stopped after processing messages.")
        print("Done!")
