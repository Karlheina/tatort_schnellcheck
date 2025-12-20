
import requests
from bs4 import BeautifulSoup

wort_zahlen = {
    "null": 0, "eins": 1, "eine": 1, "zwei": 2, "drei": 3, "vier": 4,
    "fünf": 5, "sechs": 6, "sieben": 7, "acht": 8, "neun": 9, "zehn": 10
}

# ---------------------------------------------------------
# FUNKTION: EINEN ARTIKEL PARSEN
# ---------------------------------------------------------
def parse_artikel(url):
    print("Lade Artikel:", url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # -------------------------
    # TITEL (alle Layouts)
    # -------------------------
    titel_raw = None

    # 1. Neuere Artikel: <h1>
    h1_tag = soup.find("h1")
    if h1_tag:
        titel_raw = h1_tag.get_text(strip=True)

    # 2. Neu: <strong><em>…</em></strong>
    if titel_raw is None:
        strong_em = soup.find("strong")
        if strong_em:
            em = strong_em.find("em")
            if em:
                titel_raw = em.get_text(strip=True)

    # 3. Alt: <span class="spTextSmaller"><b>…</b></span>
    if titel_raw is None:
        titel_span = soup.find("span", class_="spTextSmaller")
        if titel_span:
            b = titel_span.find("b")
            if b:
                titel_raw = b.get_text(strip=True)

    # 4. Fallback: erster <strong>, aber NICHT "Das Szenario:"
    if titel_raw is None:
        strong = soup.find("strong")
        if strong:
            text = strong.get_text(strip=True)
            if "szenario" not in text.lower():
                titel_raw = text

    # Wenn immer noch nichts gefunden wurde → Artikel überspringen
    if titel_raw is None:
        print("  Kein Titel gefunden – überspringe diesen Artikel.")
        return None

    # Titel bereinigen
    titel = (
        titel_raw
        .replace("»", "")
        .replace("«", "")
        .replace('"', "")
        .replace(",", "")
        .strip()
    )

    # -------------------------
    # STADT / ERMITTLERTEAM
    # -------------------------
    seiten_titel = None
    stadt_span = soup.find("span", class_="align-middle")
    if stadt_span:
        seiten_titel = stadt_span.get_text(strip=True)

    # -------------------------
    # JAHR
    # -------------------------
    jahr = None
    time_tag = soup.find("time", class_="timeformat")
    if time_tag and "datetime" in time_tag.attrs:
        jahr = time_tag["datetime"][:4]

    import re
    
    # -------------------------
    # BEWERTUNG (Text + Zahl)
    # -------------------------
    bewertung_text = None
    bewertung = None

    bewertung_header = soup.find(["strong", "b"], string=lambda s: s and "Bewertung" in s)
    if bewertung_header:
        p_tag = bewertung_header.find_parent().find_next("p")
        if p_tag:
            bewertung_text = p_tag.get_text(strip=True)

            # Zahl extrahieren (z. B. "3 von 10 Punkten")
            match = re.search(r"\b(\d{1,2})\b", bewertung_text)
            if match:
                bewertung = int(match.group(1))

    # -------------------------
    # RETURN BLOCK (hat gefehlt!)
    # -------------------------
    return {
        "titel": titel,
        "seiten_titel": seiten_titel,
        "jahr": jahr,
        "bewertung_text": bewertung_text,
        "bewertung": bewertung,
        "url": url
    }

# ---------------------------------------------------------
# SCHRITT 1: ALLE LINKS SAMMELN
# ---------------------------------------------------------
base_url = "https://www.spiegel.de/thema/tatort_schnellcheck/"
alle_links = set()
page = 1

while True:
    if page == 1:
        url = base_url
    else:
        url = f"{base_url}p{page}/"

    print("Lade Seite:", url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    artikel_spans = soup.find_all("span", class_="align-middle")
    links_dieser_seite = set()

    for span in artikel_spans:
        a_tag = span.find_parent("a")
        if a_tag and "href" in a_tag.attrs:
            links_dieser_seite.add(a_tag["href"])

    vorher = len(alle_links)
    alle_links.update(links_dieser_seite)
    nachher = len(alle_links)

    if nachher == vorher:
        print("Keine neuen Links mehr gefunden. Stoppe.")
        break

    page += 1

print("\nGefundene Artikel insgesamt:", len(alle_links))


# ---------------------------------------------------------
# SCHRITT 2: ARTIKEL PARSEN
# ---------------------------------------------------------
alle_artikel = []

for link in alle_links:
    daten = parse_artikel(link)
    if daten is not None:
        alle_artikel.append(daten)

print("Erfolgreich geparste Artikel:", len(alle_artikel))

import pandas as pd

# In Tabelle umwandeln
df = pd.DataFrame(alle_artikel)

# Als Excel-Datei speichern (für LibreOffice Calc geeignet)
df.to_excel("tatort_schnellcheck.xlsx", index=False)

print("Datei 'tatort_schnellcheck.xlsx' wurde erstellt.")