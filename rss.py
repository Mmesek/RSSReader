import feedparser, time, re
from bs4 import BeautifulSoup as bs
from builder import Embed
from helpers import getsizes, get_main_color
from parsers import *
def Invalid(embed, desc):
    return desc

specifics = {
    "steam": parseSteam,
    "purepc": parsePurePC,
    "cd-action": parseCDAction,
    "gg.deals": parseGGDeals,
#    "lowcygier": parseLowcy,
    "polskigamedev": polskigamdev,
    "isthereanydeal": itad,
}

class Parser:
    def __init__(self, db, src):
        self.url = src[2]
        self.last = src[1]
        self.name = src[0]
        self.feed = feedparser.parse(self.url)
        try:
            self.avatar = self.feed['feed']['image']['href']
        except:
            self.avatar = src[5]
        try:
            self.color = get_main_color(self.avatar)
        except:
            self.color = src[3]
        self.language = src[4]
        self.highest = self.last
        self.embeds = []
        self.db = db

    def entries(self):
        i=0
        for entry in self.feed['entries']:
            i += 1
            try:
                if 'youtube' in self.url:
                    current = int(time.mktime(entry["published_parsed"]))
                else:
                    current = int(time.mktime(entry["updated_parsed"]))
            except:
                current = int(time.mktime(entry["published_parsed"]))
            if current > self.highest:
                self.highest = current
            if i == 4 or current == self.last:
                self.db.update(self.name, self.highest)
                break
            elif current != self.last and current > self.last:
                try:
                    embed = self.parse(entry)
                except:
                    embed = []
                if embed != []:
                    self.embeds += [embed]

    def parse(self, entry):
        if 'gry-online' in entry['link'] and entry['category'] not in {'gry', 'sprzęt i soft'}:
            return []
        elif 'steam' in entry['link'] and 'details for this event on the' in entry['description']:
            return [] 
        desc = bs(entry.get("description", entry.get("summary", "")), "html.parser")
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
        desc_ = desc
        try:
            desc = h2tl[:2023]
        except Exception as ex:
            desc = self.last["summary_detail"]["value"]
        if "author" in entry:
            ftext = f"{entry['author']} @ {self.name}"
        else:
            ftext = self.name
        if any(s in self.url for s in ['youtube', 'nitter', 'chrono.gg']):
            desc = ''
        for s in specifics:
            if s in self.url:
                try:
                    desc = specifics.get(s, Invalid)(embed, desc, entry, desc_)
                except:
                    desc = desc
        desc = re.split(rf'(Informacja|Artykuł|The post) {re.escape(entry["title"])}', desc)[0].replace('Czytaj więcej...','')
        '''fields = []
        if len(desc) > 2023:
            des = ''
            for line in desc.splitlines(True):
                if (len(des + line) < 2023 and fields == []) or (len(des+line) < 1023 and fields != []):
                    des += line
                else:
                    fields.append(des)
                    des = ''
            if des != '':
                fields.append(des)
        else:
            fields.append(desc)
        print(len(fields))
        embed.setDescription(fields.pop(0)[:2023])
        print(len(fields))
        for field in fields:
            embed.addField('\u200b', field[:1023])'''
        embed.setFooter("", ftext).setDescription(desc[:2023])
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
