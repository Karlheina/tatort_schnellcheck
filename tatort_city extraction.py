
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

df = pd.read_excel("260215_Ermittlerteams_Wikipedia.xlsx")
series_cities = df['Region']
search_strings_cities = series_cities.dropna().astype(str).str.lower().tolist()

def extract_city(text):
    for search_string_city in search_strings_cities:
        if search_string_city in text:
            return search_string_city.capitalize()
    return None

def parse_article(url):
    logger.info('Lade Artikel: %s', url)
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')
    text = soup.get_text(" ", strip=True).lower()
    return extract_city(text)

df = pd.read_excel("tatort_schnellcheck_all articles.xlsx")
to_update = df[df['Stadt'].isna()]
logger.info(f'{len(to_update)} Artikel müssen aktualisiert werden.')

for idx, row in to_update.iterrows():
    url = row['Link']
    city = parse_article(url)
    df.at[idx, "Stadt"] = city

df.to_excel('tatort_schnellcheck_all articles_cities.xlsx', index = False)
logger.info("Datei 'tatort_schnellcheck_all articles_cities.xlsx' wurde erstellt.")