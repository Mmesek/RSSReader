import requests
import datetime
import aiohttp

import sys
import builder, database


from helpers import cumulative

db = database.Database()

config = database.ConfigToDict()
class Spotify:
    def __init__(self):
        self.rToken = config["Spotify"]["spotify"]
        self.client = config["Spotify"]["client"]
        self.secret = config["Spotify"]["secret"]
        self.auth = config["Spotify"]["auth"]
        self.token = self.refresh(self.rToken)
        self.date = str(datetime.datetime.now())

    async def spotify_call(self, path, querry, method="GET", **kwargs):
        defaults = {
            "headers": {
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        }
        kwargs = dict(defaults, **kwargs)
        response = await self.ClientSession.request(method, "https://api.spotify.com/v1/" + path + querry, **kwargs)
        try:
            return await response.json()
        except:
            return

    async def connect(self):
        self.ClientSession = aiohttp.ClientSession()

    async def disconnect(self):
        await self.ClientSession.close()

    def refresh(self, refresh_token):
        payload = {"grant_type": "refresh_token", "refresh_token": f"{refresh_token}"}
        r = requests.post(
            "https://accounts.spotify.com/api/token", data=payload, auth=(f"{self.client}", f"{self.secret}")
        )
        return r.json()["access_token"]

    async def new(self, market="gb"):
        output = []
        data = await self.spotify_call("browse/new-releases", f"?country={market}&limit=50&offset=0")
        for i in data["albums"]["items"]:
            album = await self.check(i)
            if album is not None:
                output += [album]
                # output[album['name']] = album
        return output

    async def observed(self, market="gb"):
        output = []
        artists = db.getObservedArtists()
        for one in artists:
            data = await self.spotify_call(f"artists/{one[0]}/albums", f"?market={market}&limit=50")
            for i in data["items"]:
                album = await self.check(i, one[1])
                if album is None:
                    continue
                elif album["name"] in output:
                    # output[album['name']]['artist'] += (album['artist'])
                    output += [album]
                else:
                    output += [album]
        #                    output[album['name']] = album
        return output

    async def check(self, chunk, one="Various"):
        artist = ""
        if chunk["release_date"][:10] != self.date[:10]:
            return None
        for each in chunk["artists"]:
            if each["name"] == "Various Artists":
                # artist = artist+f"[{artist}]((https://open.spotify.com/artist/{artists[one]})"
                return None
            else:
                if artist != "":
                    artist += ", "
                artist = artist + f"[{each['name']}]({each['external_urls']['spotify']})"
        uri = chunk["uri"].replace("spotify:album:", "https://open.spotify.com/album/")
        name = f"[{chunk['name']}]({uri})"  # {artist}"
        img = chunk["images"][0]["url"]
        typ = chunk["album_type"]
        group = chunk["album_type"]
        return {"name": name, "img": img, "artist": [(artist)], "type": typ, "group": group}

    async def makeList(self, market="gb"):
        result = ""
        field1, field2 = "", ""
        thumbnail = ""
        nr = await self.new(market)
        ob = await self.observed(market)
        import json
        ob2 = []
        for o in ob:
            ob2 += [json.dumps(o)]
        ob = [json.loads(o) for o in list(set(ob2))]
        ob = sorted(ob, key=lambda o: o['artist'] or "", reverse=False)
        embed = builder.Embed().setColor(1947988).setAuthor(f"New Music - {self.date[:10]}", "https://open.spotify.com/browse/discover", "https://images-eu.ssl-images-amazon.com/images/I/51rttY7a%2B9L.png")
        for item in ob:
            if 'thumbnail' not in embed.embed:
                embed.setThumbnail(ob[0]["img"])

            line = f"- {item['name']} - {item['artist'][0]}\n"

            if len(result) + len(line) < 2024:
                result += line
            else:
                tl = len(field1) + len(line)
                if (tl < 1024) and (cumulative(embed.embed) + tl < 5500):
                    field1 += line
                else:
                    if cumulative(embed.embed) + len(field1) < 5500:
                        embed.addField("\u200b", field1)
                    field1 = line
        if field1 != '':
            embed.addField("\u200b", field1)
            field1 = ''
        popular_field = False
        for item in nr:
            line = f"- {item['name']} - {item['artist'][0]}\n"
            tl = len(field2) + len(line)
            if (tl < 1024) and (cumulative(embed.embed) + tl < 5500):
                field2 += line
            else:
                if cumulative(embed.embed) + len(field2) < 5500:
                    if popular_field:
                        embed.addField("\u200b", field2)
                    else:
                        popular_field = True
                        embed.addField("Popular", field2)
                field2=line
        
        if result != "":
            embed.setDescription(result)

        return embed.embed

async def main():
    s = Spotify()
    await s.connect()
    try:
        embed = await s.makeList("pl")
    finally:
        await s.disconnect()
    build = builder.Builder("", "Spotify", "https://images-eu.ssl-images-amazon.com/images/I/51rttY7a%2B9L.png")
    build.addEmbed(embed)
    if 'description' not in embed:
        build = builder.Builder("None :(", "Spotify",None,[])
        build.send_webhook("https://discordapp.com/api/webhooks/514887726131052544/ijz16Q0fNAI7LoNUQJDl3mni1mtiCn6eWZz4fhj43fqg9o5JJl3ED9clEybkUeXlIOKg")
    elif '-webhook' in sys.argv:
        build.send_webhook("https://discordapp.com/api/webhooks/514887726131052544/ijz16Q0fNAI7LoNUQJDl3mni1mtiCn6eWZz4fhj43fqg9o5JJl3ED9clEybkUeXlIOKg")
    else:
        webhooks = db.getSpotifyWebhooks()
        for webhook in webhooks:
            build.send_webhook(webhook[0])

import asyncio
asyncio.run(main())