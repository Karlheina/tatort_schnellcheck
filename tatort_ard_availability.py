
import pandas as pd
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
    t = re.sub(r"\(\d{4}\)", "", t)   # Jahreszahlen entfernen
    t = re.sub(r"[^a-z0-9äöüß ]", " ", t)  # Sonderzeichen raus
    t = re.sub(r"\s+", " ", t)       # Mehrfache Leerzeichen
    return t.strip()

def ard_is_available(title, episodes):
    # Episodentitel aus Excel normalisieren
    if ":" in title:
        episode = title.split(":", 1)[1].strip()
    else:
        episode = title.strip()

    episode_norm = normalize_title(episode)

    matches = 0

    for ep in episodes:
        if ep.get("coreAssetType") != "EPISODE":
            continue

        ep_title_norm = normalize_title(ep.get("longTitle", ""))

        if episode_norm == ep_title_norm:
            matches +=1
            available_to = ep.get("availableTo")
            if not available_to:
                return False

            return available_to

    return False

df = pd.read_excel("tatort_schnellcheck_all articles.xlsx")
episodes = load_tatort_episodes()
df["ARD_Mediathek"] = df["Titel"].apply(lambda t: ard_is_available(t, episodes))
df.to_excel("tatort_verfuegbarkeit.xlsx", index=False)