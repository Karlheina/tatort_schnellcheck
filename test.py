
from bs4 import BeautifulSoup
import re
import requests

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

test_url = 'https://www.spiegel.de/kultur/tv/tatort-aus-muenchen-one-way-ticket-im-schnellcheck-a-1296721.html'

response = requests.get(test_url, timeout=100)
soup = BeautifulSoup(response.text, 'html.parser')

evaluation_header = soup.find(
        string=lambda s: s and 'Bewertung' in s
    )
if evaluation_header:
    p_tag = evaluation_header.find_parent().find_next('p')
    if p_tag:
        evaluation_text = p_tag.get_text(strip=True)
        evaluation = extract_evaluation(evaluation_text)

print (evaluation_text)
print (evaluation)
