import json
import os
import re
import csv
from datetime import datetime

INPUT_FILE = "collected_posts.jsonl"
CLEANED_FILE = "cleaned_data.jsonl"
TRAINING_CSV = "training_data.csv"
STATS_FILE = "data_stats.txt"

MENTAL_HEALTH_LABELS = {
    "depression": [
        "depressed", "depression", "hopeless", "worthless",
        "feeling down", "feeling sad", "no motivation",
        "cant get out of bed", "empty inside", "numb",
        "no energy", "tired of living", "giving up",
        "no point", "miserable", "unhappy", "despair",
    ],
    "anxiety": [
        "anxious", "anxiety", "panic", "panic attack",
        "worried", "worrying", "nervous", "fear",
        "scared", "overthinking", "racing thoughts",
        "cant breathe", "heart racing", "restless",
        "social anxiety", "phobia",
    ],
    "stress": [
        "stressed", "stress", "overwhelmed", "burnout",
        "burned out", "overworked", "exhausted",
        "cant cope", "breaking point", "pressure",
        "too much", "falling apart",
    ],
    "trauma": [
        "trauma", "ptsd", "flashback", "flashbacks",
        "triggered", "nightmare", "nightmares",
        "abuse", "abused", "assault", "survivor",
    ],
    "loneliness": [
        "lonely", "loneliness", "alone", "isolated",
        "isolation", "no friends", "nobody cares",
        "feel alone", "all alone", "abandoned",
    ],
    "anger": [
        "angry", "anger", "rage", "furious",
        "frustrated", "frustration", "hate",
        "resentment", "irritated",
    ],
    "self_harm": [
        "self harm", "selfharm", "cutting", "hurt myself",
        "suicidal", "suicide", "end it all", "want to die",
        "kill myself",
    ],
    "recovery": [
        "therapy", "therapist", "counseling", "counselor",
        "medication", "healing", "recovery", "getting better",
        "self care", "selfcare", "coping", "mindfulness",
        "meditation", "support group", "mental health awareness",
    ],
}

SENTIMENT_NEGATIVE = [
    "hate", "horrible", "terrible", "worst", "awful",
    "miserable", "suffering", "painful", "hurting",
    "crying", "tears", "broken", "shattered",
    "helpless", "hopeless", "worthless", "useless",
    "dying", "dead", "kill", "end",
]

SENTIMENT_POSITIVE = [
    "better", "improving", "grateful", "thankful",
    "hope", "hopeful", "healing", "recovered",
    "happy", "joy", "progress", "proud",
    "strong", "strength", "support", "helped",
    "love", "caring", "blessed", "amazing",
]

def clean_text(text):
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"@\S+", "", text)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+",
        flags=re.UNICODE,
    )
    text = emoji_pattern.sub("", text)
    text = re.sub(r"#\w+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text

def assign_labels(text):
    text_lower = text.lower()
    labels = []
    for category, keywords in MENTAL_HEALTH_LABELS.items():
        for kw in keywords:
            if kw in text_lower:
                if category not in labels:
                    labels.append(category)
                break
    return labels

def compute_sentiment(text):
    text_lower = text.lower()
    neg_count = 0
    pos_count = 0
    for word in SENTIMENT_NEGATIVE:
        if word in text_lower:
            neg_count = neg_count + 1
    for word in SENTIMENT_POSITIVE:
        if word in text_lower:
            pos_count = pos_count + 1
    if neg_count > pos_count:
        return "negative"
    elif pos_count > neg_count:
        return "positive"
    else:
        return "neutral"

def compute_severity(text, labels):
    text_lower = text.lower()
    score = 0
    if "self_harm" in labels:
        score = score + 5
    if "depression" in labels:
        score = score + 3
    if "trauma" in labels:
        score = score + 3
    if "anxiety" in labels:
        score = score + 2
    if "loneliness" in labels:
        score = score + 2
    if "stress" in labels:
        score = score + 1
    if "anger" in labels:
        score = score + 1
    severe_words = ["suicidal", "kill myself", "want to die", "end it all", "self harm"]
    for w in severe_words:
        if w in text_lower:
            score = score + 5
    distress_words = ["cant cope", "breaking point", "falling apart", "give up", "hopeless"]
    for w in distress_words:
        if w in text_lower:
            score = score + 3
    if score >= 8:
        return "high"
    elif score >= 4:
        return "medium"
    elif score >= 1:
        return "low"
    else:
        return "informational"

def load_raw_posts():
    posts = []
    if not os.path.exists(INPUT_FILE):
        print("ERROR: " + INPUT_FILE + " not found!")
        print("Run saver.py first to collect data.")
        return posts
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                post = json.loads(line)
                posts.append(post)
            except json.JSONDecodeError:
                continue
    return posts

def process_posts(posts):
    cleaned = []
    for post in posts:
        raw_content = post.get("content", "")
        clean_content = clean_text(raw_content)
        if len(clean_content) < 20:
            continue
        labels = assign_labels(clean_content)
        sentiment = compute_sentiment(clean_content)
        severity = compute_severity(clean_content, labels)
        if len(labels) == 0:
            labels = ["general_mental_health"]
        word_count = len(clean_content.split())

        record = {
            "id": post.get("id", ""),
            "created_at": post.get("created_at", ""),
            "author": post.get("author", ""),
            "raw_content": raw_content,
            "clean_content": clean_content,
            "word_count": word_count,
            "language": post.get("language", ""),
            "tags": post.get("tags", []),
            "labels": labels,
            "primary_label": labels<a href="" class="citation-link" target="_blank" style="vertical-align: super; font-size: 0.8em; margin-left: 3px;">[0]</a>,
            "sentiment": sentiment,
            "severity": severity,
            "reblogs_count": post.get("reblogs_count", 0),
            "favourites_count": post.get("favourites_count", 0),
            "replies_count": post.get("replies_count", 0),
            "url": post.get("url", ""),
        }
        cleaned.append(record)
    return cleaned

def save_cleaned_jsonl(records):
    with open(CLEANED_FILE, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("Saved " + str(len(records)) + " records to " + CLEANED_FILE)

def save_training_csv(records):
    with open(TRAINING_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "id",
            "clean_content",
            "word_count",
            "primary_label",
            "all_labels",
            "sentiment",
            "severity",
        ])
        for r in records:
            writer.writerow([
                r["id"],
                r["clean_content"],
                r["word_count"],
                r["primary_label"],
                "|".join(r["labels"]),
                r["sentiment"],
                r["severity"],
            ])
    print("Saved " + str(len(records)) + " records to " + TRAINING_CSV)

def print_stats(records):
    total = len(records)
    if total == 0:
        print("No records to analyze.")
        return

    label_counts = {}
    sentiment_counts = {}
    severity_counts = {}
    total_words = 0

    for r in records:
        for label in r["labels"]:
            if label not in label_counts:
                label_counts[label] = 0
            label_counts[label] = label_counts[label] + 1

        sent = r["sentiment"]
        if sent not in sentiment_counts:
            sentiment_counts[sent] = 0
        sentiment_counts[sent] = sentiment_counts[sent] + 1

        sev = r["severity"]
        if sev not in severity_counts:
            severity_counts[sev] = 0
        severity_counts[sev] = severity_counts[sev] + 1

        total_words = total_words + r["word_count"]

    avg_words = round(total_words / total, 1)

    stats_lines = []
    stats_lines.append("=" * 60)
    stats_lines.append("DATA PROCESSING STATS")
    stats_lines.append("=" * 60)
    stats_lines.append("Total cleaned records: " + str(total))
    stats_lines.append("Average word count: " + str(avg_words))
    stats_lines.append("")
    stats_lines.append("LABELS:")
    sorted_labels = sorted(label_counts.items(), key=lambda x: x<a href="" class="citation-link" target="_blank" style="vertical-align: super; font-size: 0.8em; margin-left: 3px;">[1]</a>, reverse=True)
    for label, cnt in sorted_labels:
        pct = round(cnt / total * 100, 1)
        bar = "#" * int(pct / 2)
        stats_lines.append("  " + label.ljust(25) + str(cnt).rjust(5) + " (" + str(pct) + "%) " + bar)
    stats_lines.append("")
    stats_lines.append("SENTIMENT:")
    for sent, cnt in sorted(sentiment_counts.items()):
        pct = round(cnt / total * 100, 1)
        stats_lines.append("  " + sent.ljust(15) + str(cnt).rjust(5) + " (" + str(pct) + "%)")
    stats_lines.append("")
    stats_lines.append("SEVERITY:")
    for sev, cnt in sorted(severity_counts.items()):
        pct = round(cnt / total * 100, 1)
        stats_lines.append("  " + sev.ljust(15) + str(cnt).rjust(5) + " (" + str(pct) + "%)")
    stats_lines.append("")
    stats_lines.append("OUTPUT FILES:")
    stats_lines.append("  " + CLEANED_FILE + " - Full cleaned data (JSONL)")
    stats_lines.append("  " + TRAINING_CSV + " - Training-ready CSV")
    stats_lines.append("  " + STATS_FILE + " - This stats report")
    stats_lines.append("=" * 60)

    report = "\n".join(stats_lines)
    print(report)

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        f.write(report)
    print("\nStats saved to " + STATS_FILE)

def main():
    print("=" * 60)
    print("MASTODON DATA PREPROCESSOR FOR AI TRAINING")
    print("=" * 60 + "\n")

    print("Step 1: Loading raw posts from " + INPUT_FILE + "...")
    raw_posts = load_raw_posts()
    print("  Loaded " + str(len(raw_posts)) + " raw posts\n")

    if len(raw_posts) == 0:
        print("No data to process. Run saver.py first!")
        return

    print("Step 2: Cleaning and labeling...")
    cleaned = process_posts(raw_posts)
    print("  Cleaned " + str(len(cleaned)) + " posts (removed " + str(len(raw_posts) - len(cleaned)) + " short/empty)\n")

    print("Step 3: Saving cleaned data...")
    save_cleaned_jsonl(cleaned)
    save_training_csv(cleaned)
    print("")

    print("Step 4: Computing stats...")
    print_stats(cleaned)

    print("\n\nDONE! Your data is ready for AI training.")
    print("")
    print("NEXT STEPS:")
    print("  1. Use training_data.csv for classification models")
    print("  2. Use cleaned_data.jsonl for NLP/transformer models")
    print("  3. Primary labels: depression, anxiety, stress, trauma, etc.")
    print("  4. Sentiment: positive, negative, neutral")
    print("  5. Severity: high, medium, low, informational")

if __name__ == "__main__":
    main()
