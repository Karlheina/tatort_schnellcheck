
import logging
import pandas as pd
import requests
from bs4 import BeautifulSoup

df = pd.read_excel("260215_Ermittlerteams_Wikipedia.xlsx")
search_string_city = df['Region']
print(type(df))