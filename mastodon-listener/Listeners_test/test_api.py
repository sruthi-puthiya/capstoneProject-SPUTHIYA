import requests

INSTANCE_URL = "https://mastodon.social"
ACCESS_TOKEN = "PUT_YOUR_TOKEN_HERE"

headers = {"Authorization": "Bearer " + ACCESS_TOKEN}

endpoints = [
    "/api/v1/timelines/public",
    "/api/v1/timelines/public?local=true",
    "/api/v1/timelines/tag/mentalhealth",
    "/api/v1/timelines/tag/depression",
    "/api/v1/timelines/tag/anxiety",
    "/api/v1/trends/statuses",
]

for ep in endpoints:
    url = INSTANCE_URL + ep
    try:
        resp = requests.get(url, headers=headers, params={"limit": 5}, timeout=10)
        data = resp.json()
        if isinstance(data, list):
            print("  " + ep + " => " + str(len(data)) + " posts")
        else:
            print("  " + ep + " => " + str(data))
    except Exception as e:
        print("  " + ep + " => ERROR: " + str(e))
