import re

def extract_episode_title(text):
    if not text:
        return None

    # Entferne äußere Leerzeichen und Kommas
    cleaned = text.strip().strip(',')

    # Wenn "Tatort:" oder "Polizeiruf:" enthalten ist → alles danach ist der Episodentitel
    for prefix in ["Tatort:", "Polizeiruf:"]:
        if prefix in cleaned:
            return cleaned.split(prefix, 1)[1].strip()

    # Finde ALLE Titel in Anführungszeichen (alle Varianten)
    quote_pattern = r'[\"\'»«„“](.*?)[\"\'«»“”]'
    matches = re.findall(quote_pattern, cleaned)

    if matches:
        return matches[-1].strip()  # Nimm den letzten Treffer

    # Fallback: Titel nach dem letzten Doppelpunkt
    if ":" in cleaned:
        return cleaned.rsplit(":", 1)[-1].strip()

    return cleaned

title = extract_episode_title('»Tatort: In der Familie (2)«')
print(title)