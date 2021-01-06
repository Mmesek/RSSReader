import requests, random, json
from bs4 import BeautifulSoup
from datetime import datetime

from builder import Builder, Embed
from database import Database
import sys
from os.path import dirname
with open(dirname(__file__)+"/steamstoreindex.json", "r") as file:
    steam_games = json.load(file)

def get_today(today):
    days = ''
    try:
        days += parse_kalbi_main(request_url("https://www.kalbi.pl"))
    except:
        pass
    if days != '':
        days += "\n"

    month = today.month
    day = today.day
    if month <= 9:
        month = "0" + str(month)
    if day <= 9:
        day = "0" + str(day)

    try:
        days += parse_daysoftheyear(request_url(f"https://www.daysoftheyear.com/days/{today.year}/{month}/{day}/"))
    except:
        pass
    return days

def get_game_releases(today):
    return parse_gryonline(request_url("https://www.gry-online.pl/daty-premier-gier.asp?PLA=1"), today)

def get_movie_releases(today):
    return '' #parse_imdb(request_url("https://www.imdb.com/calendar?region=PL"), today)

def get_tv_shows(today):
    return ''

def request_url(query):
    r = requests.get(
        query,
        headers={"user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"},
    )
    if r.status_code == 200:
        return BeautifulSoup(r.content, "html.parser")
    else:
        return

def parse_daysoftheyear(soup):
    f = ""
    for p in soup.find_all("h3", class_="card__title heading"):
        if "week" in p.text.lower() or "month" in p.text.lower():
            continue
        else:
            f += "\n- " + p.text
    return f

def parse_kalbi(soup):
    soup = soup.find("article", class_="unusual-day")
    f = ""
    for d in soup.find_all("div", class_="description-of-holiday"):
        f += "\n- " + d.find("h3").text
    return f

def parse_kalbi_main(soup):
    _names = ""
    names = soup.find("div", class_="calCard-name-day")
    for name in names.find_all("a"):
        _names += "\n- " + name.text.strip()
    holiday = soup.find("div", class_="calCard-fete holyday")
    try:
        _days = "\n- " + holiday.text.strip()
    except:
        _days = ""
    days = soup.find("div", class_="calCard-ententa")
    for day in days.find_all("a"):
        _days += "\n- " + day.text.strip()
    return _days

def parse_gryonline(soup, today):
    soup = soup.find('div',class_='daty-premier-2017')
    games = ''
    for release in soup.find_all('a', class_='box'):
        lines = release.find_all('div')
        release_date = lines[0].text
        if str(today.day) not in release_date:
            break
        p = release.find('p', class_='box-sm')
        previous_release = None
        if p:
            previous_release = p.text.replace('PC','')
        game = lines[1].contents[0]
        platform = lines[-1].text.replace(', Pudełko', '')
        if "Steam" in platform or "Wczesny dostęp" in platform:
            steamid =  steam_games.get(game.strip(), "")
            if steamid != "":
                platform = platform.replace('Steam', f'[Steam](https://store.steampowered.com/app/{steamid})').replace("Wczesny dostęp", f'[Wczesny dostęp](https://store.steampowered.com/app/{steamid})')
        games += f'\n- {game} ({platform})'
        if previous_release is not None:
            games += ' | Poprzednio wydane:\n*' + previous_release.replace('\n\n', ' - ').replace('\n', '') + '*'
    return games

def parse_ign(soup, today):
    soup = soup.find('div', class_='jsx-3629687597 four-grid')
    if soup == None:
        return ''
    movies = ''
    for movie in soup.find_all('a', class_='card-link'):
        lines = movie.find('div', class_='jsx-2539949385 details')#.find_all('div')
        release = lines.find('div', class_='jsx-2539949385 release-date').text
        if today.strftime("%b %d, %Y").replace(' 0', ' ') not in release:
            continue
        name = lines.find('div', class_='jsx-2539949385 name').text
        platform = lines.find('div', class_='jsx-2539949385 platform').text
        movies += f'\n- {name}'  #({platform})'
    return movies

def parse_imdb(soup, today):
    return ""

def add_quote(today, embed):
    random.seed(today.isoformat()[:10])  # hash(today.year / today.month + today.day))
    with open(dirname(__file__)+"/quotes.json", "r", newline="", encoding="utf-8") as file:
        q = json.load(file)
    quote = random.choice(q)
    embed.setFooter("", quote["text"] + "\n- " + quote["author"])

today = datetime.now()

embed = Embed().setTitle(today.strftime(f"%A, %B %Y (%m/%d)"))
#embed.setTimestamp(datetime.now(tz=timezone.utc).isoformat())

today_days = get_today(today)
embed.setDescription(today_days)

games = get_game_releases(today)
movies = get_movie_releases(today)
tv_shows = get_tv_shows(today)

if games != '':
    embed.addFields("Game releases", games, True)

if movies != '':
    embed.addFields("Movie releases", movies, True)

if tv_shows != '':
    embed.addFields("TV Show Episodes", tv_shows, True)

add_quote(today, embed)
embed.setColor(random.randint(0, 16777215))

build = Builder()
build.addEmbed(embed.embed)
db = Database()
if '-webhook' in sys.argv:
    build.send_webhook("514887726131052544/ijz16Q0fNAI7LoNUQJDl3mni1mtiCn6eWZz4fhj43fqg9o5JJl3ED9clEybkUeXlIOKg")
else:
    for webhook in db.getTodayWebhooks():
        build.send_webhook(webhook[0])
