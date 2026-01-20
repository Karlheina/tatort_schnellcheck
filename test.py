
import pandas as pd
from datetime import datetime, timezone
import re
import requests

def load_tatort_episodes():
    episodes = []
    page = 0

    while True:
        url = (
            "https://api.ardmediathek.de/page-gateway/widgets/ard/asset/"
            "Y3JpZDovL2Rhc2Vyc3RlLmRlL3RhdG9ydA"
            f"?pageNumber={page}&pageSize=24"
        )

        data = requests.get(url, timeout=10).json()
        teasers = data.get("teasers", [])

        if not teasers:
            break

        episodes.extend(teasers)
        page += 1

    return episodes
    
def normalize_title(t):
    if not t:
        return ""
    t = t.lower()
    t = re.sub(r"\(\d{4}\)", "", t)
    t = re.sub(r"[^a-z0-9äöüß ]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def ard_available_to(title, episodes):
    if ":" in title:
        episode = title.split(":", 1)[1].strip()
    else:
        episode = title.strip()

    episode_norm = normalize_title(episode)

    for ep in episodes:
        if ep.get("coreAssetType") != "EPISODE":
            continue

        ep_title_norm = normalize_title(
            ep.get("longTitle") or ep.get("title") or ""
        )

        if episode_norm == ep_title_norm:
            return ep.get("availableTo")

    return None

df = pd.read_excel("tatort_schnellcheck_test articles.xlsx")
episodes = load_tatort_episodes()
df["ARD_availableTo"] = df["Titel"].apply(lambda t: ard_available_to(t, episodes))
df.to_excel("tatort_verfuegbarkeit.xlsx", index=False)