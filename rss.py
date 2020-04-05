import feedparser, time, re, html2text
from bs4 import BeautifulSoup as bs
from builder import Embed
from helpers import getsizes
from parsers import *
def Invalid(embed, desc):
    return desc

def nitter(embed, entry, feed, desc):
    if entry["author"] == "@DyingLightGame":
        embed.setUrl(entry["link"].replace("nitter.net", "twitter.com")).setTitle(feed["title"]).setAuthor(
            entry["author"], feed["link"].replace("nitter.net", "twitter.com"), feed["image"]["url"]
        ).setDescription(entry["title"])
    else:
        return []
    return desc

def steam(embed, desc):
    h2t = html2text.HTML2Text()
    h2tl = (
        h2t.handle(desc.prettify())
        .replace("\n [", "[")
        .replace("\n]", "]")
        .replace("[ ", "[")
        .replace("{LINK REMOVED}", "")
        .replace("\n\n", "\n")
    )
    try:
        if desc.img["src"][-4:] != ".gif":
            imag = desc.img["src"]
    except:
        imag = ''
    links_all = re.findall(r"\((https://store.steam\S*)\)\s", h2tl)
    for link in links_all:
        s = link.split("/")[-2].replace("_", " ")
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link}]({link})", "")
        embed.addField("Steam Store", f"[{s}]({link})", True)
    events = re.findall(r"\((\S*/partnerevents/view/\S*)\)\s", h2tl)
    for link in events:
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link}]({link})", "")
        embed.addField("Steam Event", f"[View Event]({link})", True)
    embed.setImage(imag)
    return desc

specifics = {
    "steam": parseSteam,
    "purepc": parsePurePC,
    "cd-action": parseCDAction,
    "gg.deals": parseGGDeals,
}

class Parser:
    def __init__(self, db, src):
        self.url = src[2]
        self.last = src[1]
        self.name = src[0]
        self.color = src[3]
        self.language = src[4]
        self.highest = self.last
        self.embeds = []
        self.feed = feedparser.parse(self.url)
        self.db = db

    def entries(self):
        i=0
        for entry in self.feed['entries']:
            i += 1
            try:
                current = int(time.mktime(entry["updated_parsed"]))
            except:
                current = int(time.mktime(entry["published_parsed"]))
            if current > self.highest:
                self.highest = current
            if i == 4 or current == self.last:
                self.db.update(self.name, self.highest)
                break
            elif current != self.last and current > self.last:
                embed = self.parse(entry)
                if embed != []:
                    self.embeds += [embed]

    def parse(self, entry):
        if 'gry-online' in entry['link'] and entry['category'] not in {'gry', 'sprzęt i soft'}:
            return []
        desc = bs(entry["description"], "html.parser")
        embed = Embed()
        embed.setColor(self.color)
        try:
            embed.setTimestamp(time.strftime("%Y-%m-%dT%H:%M:%S", entry["published_parsed"]))
        except:
            embed.setTimestamp(time.strftime("%Y-%m-%dT%H:%M:%S", entry["updated_parsed"]))
        embed.setTitle(entry["title"]).setUrl(entry["link"].replace('nitter.net','twitter.com'))
        h2tl = desc.text
        try:
            imag = desc.find("img")["src"]
            try:
                if h2tl == '':
                    h2tl = desc.img['alt']
            except:
                pass
        except:
            imag = ''
        h2tl = h2tl.replace(f"![]({imag})  \n  \n", "")
        images = re.findall(r"\!\[\]\(\S*\)", h2tl)
        for image in images:
            h2tl = h2tl.replace(f"{image}", "")
        #desc = specifics.get(self.name, Invalid)(embed, desc)
        #if 'steam' in self.url:
            #desc = parseSteam(embed, desc)

        #desc = steam(embed, desc)
        desc_ = desc
        try:
            desc = h2tl[:2023]
        except Exception as ex:
            desc = self.last["summary_detail"]["value"]
        if "author" in entry:
            ftext = f"{entry['author']} @ {self.name}"
        else:
            ftext = self.name
        if any(s in self.url for s in ['youtube', 'nitter']):
            desc = ''
        for s in specifics:
            if s in self.url:
                desc = specifics.get(s, Invalid)(embed, desc, entry, desc_)
        embed.setFooter("", ftext).setDescription(desc[:2023])#.replace(" * ", "\n").replace("______", "-")[:2023])
        if imag !='':
            size = getsizes(imag)
            if (size[1][0] == size[1][1] and size[1][0] < 800) or size[1][0] < 400:
                embed.setThumbnail(imag)
            else:
                embed.setImage(imag)
        else:
            try:
                embed.setThumbnail(entry['media_thumbnail'][0]['url'])
            except:
                pass

        return embed.embed
