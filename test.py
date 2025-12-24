import re
from bs4 import BeautifulSoup

def extract_title_from_page_end(soup):
    text = soup.get_text(" ", strip=True)

    prefixes = ["Tatort:", "Polizeiruf:"]

    candidates = []

    for prefix in prefixes:
        if prefix in text:
            after = text.split(prefix, 1)[1].strip()

            m = re.search(r'[\"»„“](.*?)[\"«”]', after)
            if m:
                candidates.append(prefix + " " + m.group(1).strip())
                continue

            m = re.match(r'([^.,;!?]+)', after)
            if m:
                candidates.append(prefix + " " + m.group(1).strip())
                continue

            first_word = after.split()[0]
            candidates.append(prefix + " " + first_word)

    if not candidates:
        return None

    return max(candidates, key=len)

test_titles = [
    "Tatort: „Der dunkle Wald“",
    "Polizeiruf: Der stille Gast",
    "Tatort: Ein Fall ohne Anführungszeichen",
    "Tatort: Der Wald – Ein neuer Fall",
    "Kein Tatort hier"
    "»Tatort: Murot und das 1000-jährige Reich«, Sonntag, 20.15 Uhr, Das Erste"
]

for t in test_titles:
    soup = BeautifulSoup(f"<p>{t}</p>", "html.parser")
    print(t, "→", extract_title_from_page_end(soup))