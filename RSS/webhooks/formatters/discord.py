import re

from bs4 import BeautifulSoup as bs
from mdiscord import Embed, Limits as DiscordLimits

from RSS.models import Feed_Post
from RSS.utils import RE_IMAGE_URL
from RSS.webhooks.models import Subscription

from . import Limits as BaseLimits, Request


class Limits(BaseLimits):
    EMBEDS = 10
    CONTENT = 2000
    TOTAL = 6000


def toMarkdown(html: str) -> str:
    import html2text

    h2tl = html2text.HTML2Text(bodywidth=0)
    h2tl.protect_links = True
    h2tl.single_line_break = True
    return h2tl.handle(html).replace("\n\n", "\n")


class Discord(Request):
    content: str = ""
    username: str = None
    avatar_url: str = None
    embeds: list[Embed] = None

    def __init__(self, sub: Subscription, entries: list["Feed_Post"]) -> None:
        if (sub.content or "") not in self.content and len(self.content) < Limits.CONTENT:
            self.content += " " + toMarkdown(sub.content)
            self.content = self.content.strip()
        if not self.username:
            self.username = sub.feed.name
        if not self.avatar_url:
            self.avatar_url = sub.feed.icon_url
        self.embeds = []

        for entry in entries:
            embed = Embed()
            embed.set_title(entry.title)
            embed.set_footer(entry.author)
            embed.set_url(entry.url)
            embed.set_timestamp(entry.timestamp)

            embed.set_color(entry.feed.color)
            embed.set_image(entry.thumbnail_url)

            description = entry.content or entry.summary

            soup = bs(description, "lxml")
            img = soup.find("img")
            if not embed.image.url and img and not img.get("src", "").endswith("gif"):
                embed.image.url = img.get("src", "")
            description = toMarkdown(description).strip()

            image = RE_IMAGE_URL.search(description)
            if not embed.image.url and image:
                embed.image.url = image
            description = RE_IMAGE_URL.sub(image.group(1) if image else "", description)
            description = re.split(rf"(Informacja|Artykuł|The post) \[?{re.escape(embed.title)}", description)[0]
            description = description.replace("Czytaj więcej...", "").replace("Czytaj dalej", "")

            entry.description = description

            if len(description) <= DiscordLimits.DESCRIPTION:
                embed.set_description(description)
            else:
                embed.add_fields("\u200b", description)

            self.embeds.append(embed.as_dict())
