import requests

class Embed:
    def __init__(self):
        self.embed = {"fields": []}

    def setTitle(self, title):
        self.embed['title'] = title
        return self

    def setDescription(self, description):
        self.embed['description'] = description
        return self

    def setColor(self, color):
        self.embed['color'] = color
        return self

    def setUrl(self, url):
        self.embed['url'] = url
        return self

    def setImage(self, url):
        self.embed['image'] = {"url": url}
        return self

    def setThumbnail(self, url):
        self.embed['thumbnail'] = {"url": url}
        return self

    def setFooter(self, icon, text):
        self.embed['footer'] = {"icon_url": icon, "text": text}
        return self

    def setTimestamp(self, timestamp):
        self.embed['timestamp'] = timestamp
        return self

    def setAuthor(self, name, url, icon):
        self.embed['author'] = {"name": name, "url": url, "icon_url": icon}
        return self

    def addField(self, name, value, inline=False):
        self.embed['fields'] += [{"name": name,
        "value": value, "inline": inline}]
        return self

import time
class Builder:
    def __init__(self, content='', username=None, avatar_url=None, embeds: list=[]):#(Embed)=[]):
        self.content = content
        self.username = username
        self.avatar_url = avatar_url
        self.embeds = embeds
        self._lock = False

    def addEmbed(self, embed):
        self.embeds += [embed]
    def addEmbeds(self, embeds):
        self.embeds += embeds
    def send_(self, url, json):
        if self._lock == False:
            r = requests.post(url, json=json)
            try:
                r = r.json()
            except:
                r = r.reason
            #print(r)
            if 'retry_after' in r:
                self._lock = True
                #print('sleeping')
                time.sleep(r['retry_after']/1000)
                self._lock = False
                return self.send_(url, json)
        else:
            time.sleep(0.5)
            return self.send_(url, json)


    def send_webhook(self, url):
        json = {"content": self.content, "embeds": self.embeds, "username": self.username, "avatar_url": self.avatar_url}
        return self.send_(url, json)
        r = requests.post(url, json=json)
        try:
            r = r.json()
        except:
            r = r.reason
        print(r)
