from . import Entry, Limits as BaseLimits, Request
from RSS.webhooks.models import Subscription
from mdiscord import Embed, Limits as DiscordLimits


class Discord(BaseLimits, DiscordLimits):
    EMBEDS = 10


def toMarkdown(html: str) -> str:
    import html2text

    h2tl = html2text.HTML2Text(bodywidth=0)
    h2tl.protect_links = True
    h2tl.single_line_break = True
    return h2tl.handle(html).replace("\n\n", "\n")


class Discord(Request):
    content: str
    username: str
    avatar_url: str
    embeds: list[Embed]

    def __init__(self, sub: Subscription, entries: list[Entry]) -> None:
        if (sub.content or "") not in self.content:
            self.content += " " + toMarkdown(sub.content)
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
            entry.description = toMarkdown(entry.description)

            if len(entry.description) <= DiscordLimits.DESCRIPTION:
                embed.set_description(entry.description)
            else:
                embed.add_fields("\u200b", entry.description)

            self.embeds.append(embed.as_dict())
