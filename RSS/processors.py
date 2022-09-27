import requests
from bs4 import BeautifulSoup as bs

from .utils import Entry, processor

HEADERS = {'Accept': 'text/html', 'User-Agent': 'Mozzila'}

@processor
def blacklist(entry: Entry, value: str) -> bool:
    if value in entry.embed.description:
        return False
    return True

@processor
def make_list(entry: Entry, value: str) -> bool:
    if value in entry.embed.title:
        r = requests.get(entry.embed.url, headers=HEADERS)
        soup = bs(r.text, 'lxml')
        article = soup.find('div', itemprop='articleBody')
        #glist = soup.find('div', class_='main').findAll('li')
        headers = article.findAll('h2')
    return True

@processor
def include_content(entry: Entry, value: str) -> bool:
    import newspaper
    _ = newspaper.Article(entry.embed.url) #, MAX_TEXT=Limits.TOTAL, MAX_FILE_MEMO=100, fetch_images=False)
    _.download()
    _.parse()
    entry.embed.setDescription()