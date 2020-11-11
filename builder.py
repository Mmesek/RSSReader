import requests

class Embed:
    def __init__(self):
        self.embed = {"fields": []}
        self.total_characters = 0

    def setTitle(self, title):
        if self.total_characters + len(str(title)) <= 6000:
            self.embed['title'] = title
            self.total_characters += len(str(title))
        return self

    def setDescription(self, description):
        description = str(description)[:2024]
        if self.total_characters + len(str(description)) <= 6000:
            self.embed['description'] = description
            self.total_characters += len(str(description))
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
        if self.total_characters + len(str(text)) <= 6000:
            self.embed['footer'] = {"icon_url": icon, "text": text}
            self.total_characters += len(str(text))
        return self

    def setTimestamp(self, timestamp):
        self.embed['timestamp'] = timestamp
        return self

    def setAuthor(self, name, url, icon):
        if self.total_characters + len(str(name)) <= 6000:
            self.embed['author'] = {"name": name, "url": url, "icon_url": icon}
            self.total_characters += len(str(name))
        return self

    def addField(self, name, value, inline=False):
        value = str(value)[:1024]
        if self.total_characters + len(str(name)) + len(str(value)) <= 6000:
            self.embed['fields'] += [{"name": name,
                                      "value": value, "inline": inline}]
            self.total_characters += len(str(name)) + len(str(value))
        return self
    
    def addFields(self, title, text, inline=False):
        from textwrap import wrap
        for x, chunk in enumerate(wrap(text, 1024, replace_whitespace=False)):
            if len(self.fields) == 25:
                break
            #if x == 0 and (len(title) + len(chunk) + self.total_characters) < 6000:
            if x == 0:
                self.addField(title, chunk, inline)
            #elif (len('\u200b') + len(chunk) + self.total_characters) < 6000:
            else:
                self.addField('\u200b', chunk, inline)
        return self
    
    @property
    def fields(self):
        return self.embed.get('fields', [])

    @property
    def description(self):
        return self.embed.get('description','')

import time
class Builder:
    def __init__(self, content='', username=None, avatar_url=None, embeds: list = []):  #(Embed)=[]):
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
                time.sleep(r['retry_after']/1000)
                self._lock = False
                return self.send_(url, json)
        else:
            time.sleep(0.5)
            return self.send_(url, json)


    def send_webhook(self, url):
        json = {"content": self.content, "embeds": self.embeds, "username": self.username, "avatar_url": self.avatar_url}
        return self.send_("https://discordapp.com/api/webhooks/"+url, json)
