# config.py

INSTANCE_URL = "https://mastodon.social"

KAFKA_BOOTSTRAP_SERVERS = ["localhost:9092"]
KAFKA_TOPIC_RAW = "mastodon.raw.posts"
KAFKA_TOPIC_FILTERED = "mastodon.filtered.mental_health"
KAFKA_CONSUMER_GROUP = "mental-health-listener"

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
POLL_INTERVAL_SECONDS = 15
FETCH_LIMIT_PER_TAG = 20
