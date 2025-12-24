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

def find_raw_title_in_html(soup):
    page_text = soup.get_text(" ", strip=True)

    prefix_series = ["Tatort:", "Polizeiruf:"]
    for prefix in prefix_series:
        if prefix in page_text:
            raw_title = page_text.split(prefix, 1)[1].strip()
            return prefix, raw_title

    return None, None

def clean_episode_title(prefix, raw_title):
    if not raw_title:
        return None

    if ", Sonntag" in raw_title:
        return f"{prefix} {raw_title.split(', Sonntag', 1)[0].strip()}"

    m = re.search(r'[\"»„“](.*?)[\"«”]', raw_title)
    if m:
        return f"{prefix} {m.group(1).strip()}"
    
    return f"{prefix} {raw_title}"
    
def extract_episode_title(soup):
    prefix, raw_title = find_raw_title_in_html(soup)
    if not raw_title:
        return None
    return clean_episode_title(prefix, raw_title)

def parse_article(url):
    logger.info('Lade Artikel: %s', url)
    response = requests.get(url, timeout=100)
    soup = BeautifulSoup(response.text, 'html.parser')

    h1_tag = soup.find('h1')

    title_raw = extract_episode_title(soup)
    if not title_raw:
        logger.info("Kein Titel gefunden – überspringe Artikel.")
        return None

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
        ['strong', 'b'], string=lambda s: s and 'Bewertung' in s
    )
    if evaluation_header:
        p_tag = evaluation_header.find_parent().find_next('p')
        if p_tag:
            evaluation_text = p_tag.get_text(strip=True)

            match = re.search(r'\b(\d{1,2})\b', evaluation_text)
            if match:
                evaluation = int(match.group(1))

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