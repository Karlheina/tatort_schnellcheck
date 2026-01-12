import logging
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger('tatort_copilot')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

NUMBER_WORDS = {
    "null": 0,
    "eins": 1, "eine": 1, "einem": 1, "einen": 1,
    "zwei": 2,
    "drei": 3,
    "vier": 4,
    "fünf": 5,
    "sechs": 6,
    "sieben": 7,
    "acht": 8,
    "neun": 9,
    "zehn": 10,
}

def extract_title_from_bottom(soup):
    page_text = soup.get_text(" ", strip=True)

    for prefix in ["Tatort:", "Polizeiruf:", "Polizeiruf 110:"]:
        if prefix not in page_text:
            continue

        # 1. Fall: Anführungszeichen VOR dem Präfix
        m_outer = re.search(r'[\"»„“]\s*' + prefix + r'\s*(.*?)[\"«”]', page_text)
        if m_outer:
            return f"{prefix} {m_outer.group(1).strip()}"

        # 2. Normalfall: Text nach dem Präfix
        raw_title = page_text.rsplit(prefix, 1)[1].strip()

        # 3. Endmarker: 20:15 oder andere Uhrzeiten
        m_time = re.search(r'(.*?)(\d{1,2}[:.]\d{2})', raw_title)
        if m_time:
            return f"{prefix} {m_time.group(1).strip()}"

        # 5. Titel in Anführungszeichen
        m_inner = re.search(r'[\"»„“](.*?)[\"«”]', raw_title)
        if m_inner:
            return f"{prefix} {m_inner.group(1).strip()}"

        # 6. Fallback
        return f"{prefix} {raw_title}"

    return None

def extract_title_from_h1(soup):
    h1 = soup.find("h1")
    if not h1:
         return None
     
    text = h1.get_text(" ", strip=True)

    m = re.search(r'[»„“"]\s*Tatort\s*[«“”"]\D*?[»„“"](.+?)[«“”"]', text)
    if m:
        return f"Tatort: {m.group(1).strip()}"
    
    m = re.search(r'Tatort[^\w]+[»„“"](.+?)[«“”"]', text)
    if m:
        return f"Tatort: {m.group(1).strip()}"
    
    m = re.search(r'Polizeiruf.*?:\s*([A-Za-zÄÖÜäöüß0-9\- ]+)', text)
    if m:
        return f"Polizeiruf: {m.group(1).strip()}"
    
    return None

def extract_evaluation(evaluation_text):
    m = re.search(r'(\w+)\s+von\b', evaluation_text.lower())
    if not m:
        return None

    first_part = m.group(1)

    if first_part.isdigit():
        return int(first_part)

    if first_part in NUMBER_WORDS:
        return NUMBER_WORDS[first_part]

    return None

def parse_article(url):
    logger.info('Lade Artikel: %s', url)
    response = requests.get(url, timeout=100)
    soup = BeautifulSoup(response.text, 'html.parser')

    h1_tag = soup.find('h1')

    title_raw = extract_title_from_bottom(soup) 

    if not title_raw:
        title_raw = extract_title_from_h1(soup)

    
    if not title_raw:
        logger.info("Kein Titel gefunden für URL: %s", url)
        title = None

    else:
        title = title_raw.strip()

    def extract_city_from_h1(h1_text):
        words = h1_text.split()
        for i, w in enumerate(words):
            if w.lower() == "aus" and i + 1 < len(words):
                return words[i + 1].strip('":«»„“')
        return None

    city = None
    if 'h1_tag' in locals() and h1_tag:
        h1_text = h1_tag.get_text(strip=True)
        city = extract_city_from_h1(h1_text)

    def extract_city_from_h1(h1_text):
        words = h1_text.split()
        for i, w in enumerate(words):
            if w.lower() == "aus" and i + 1 < len(words):
                return words[i + 1].strip('":«»„“')
        return None

    city = None
    if h1_tag:
        h1_text = h1_tag.get_text(strip=True)
        city = extract_city_from_h1(h1_text) 

    year = None
    time_tag = soup.find('time', class_='timeformat')
    if time_tag and 'datetime' in time_tag.attrs:
        year = time_tag['datetime'][:4]

    evaluation_text = None
    evaluation = None

    evaluation_header = soup.find(
        string=lambda s: s and 'Bewertung' in s
    )
    if evaluation_header:
        p_tag = evaluation_header.find_parent().find_next('p')
        if p_tag:
            evaluation_text = p_tag.get_text(strip=True)
            evaluation = extract_evaluation(evaluation_text)

    return {
        'Titel': title,
        'Stadt': city,
        'Jahr': year,
        'Bewertungstext': evaluation_text,
        'Bewertung': evaluation,
        'Link': url,
    }

def collect_links(base_url):
    all_links = set()
    page = 1

    while True:
        url = base_url if page == 1 else f'{base_url}p{page}/'

        logger.info('Lade Seite: %s', url)
        response = requests.get(url, timeout=100)
        soup = BeautifulSoup(response.text, 'html.parser')

        article_spans = soup.find_all('span', class_='align-middle')
        links_of_this_page = set()

        for span in article_spans:
            a_tag = span.find_parent('a')
            if a_tag and 'href' in a_tag.attrs:
                links_of_this_page.add(a_tag['href'])

        before = len(all_links)
        all_links.update(links_of_this_page)
        after = len(all_links)

        if after == before:
            logger.info('Keine neuen Links mehr gefunden. Stoppe.')
            break

        page += 1

    logger.info('\nGefundene Artikel insgesamt: %d', len(all_links))
    return all_links

def scrape_all_articles(links):
    all_articles = []

    for link in links:
        data = parse_article(link)
        if data is not None:
            all_articles.append(data)

    logger.info('Erfolgreich geparste Artikel: %d', len(all_articles))
    return all_articles

def save_to_table (data, filename):
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    logger.info("Datei 'tatort_schnellcheck.xlsx' wurde erstellt.")

def run_scraper():
    base_url = 'https://www.spiegel.de/thema/tatort_schnellcheck/'
    links = collect_links(base_url)
    articles = scrape_all_articles(links)
    save_to_table(articles, "tatort_schnellcheck.xlsx")

if __name__ == "__main__":
    run_scraper()