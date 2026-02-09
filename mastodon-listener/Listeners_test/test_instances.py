import requests

instances = [
    "https://mastodon.social",
    "https://mas.to",
    "https://mastodon.world",
    "https://techhub.social",
    "https://mstdn.social",
]

for inst in instances:
    url = inst + "/api/v1/timelines/public"
    try:
        resp = requests.get(url, params={"limit": 3}, timeout=10)
        data = resp.json()
        if isinstance(data, list):
            count = len(data)
            if count > 0:
                sample = data<a href="" class="citation-link" target="_blank" style="vertical-align: super; font-size: 0.8em; margin-left: 3px;">[0]</a>.get("content", "")[:60]
                print("  " + inst + " => " + str(count) + " posts  (WORKS!)")
            else:
                print("  " + inst + " => 0 posts")
        else:
            err = str(data)[:80]
            print("  " + inst + " => " + err)
    except Exception as e:
        print("  " + inst + " => ERROR: " + str(e))
