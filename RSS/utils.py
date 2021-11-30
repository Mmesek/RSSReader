import time, functools

from typing import Callable, TYPE_CHECKING, Dict, List
from itertools import groupby
from datetime import datetime#, timezone

import feedparser
from bs4 import BeautifulSoup as bs

from mdiscord import Embed, Embed_Field, Limits

if TYPE_CHECKING:
    from .models import Feed, Webhook

import re
RE_IMAGE_URL = re.compile(r"\[?\!\[(.*?)\]\(\S*\)")

processors: Dict[str, Callable] = {}
"""Registered Processors for RSS Sources"""

pre_processors: Dict[str, Callable] = {}
"""Registered Pre Processors (Cleaning) for RSS Entries"""

post_processors: Dict[str, Callable] = {}
"""Registered Post Processors (Summarizing, Extracting) for RSS Entries"""

def processor(cls: Callable=None, source: str = None, registry: Dict[str, Callable]=processors):
    """Adds new processor to source"""
    @functools.wraps(cls)
    def inner(f: Callable):
        # TODO: Consider turning it into a list like onDispatch and iterate over instead of calling single one
        registry[source or f.__name__] = f
        return f
    if cls:
        return inner(cls)
    return inner

def toMarkdown(html: str) -> str:
    import html2text
    h2tl = html2text.HTML2Text(bodywidth=0)
    h2tl.protect_links = True
    h2tl.single_line_break = True
    return h2tl.handle(html).replace("\n\n", "\n")


class Entry:
    """Processed Feed Entry formatted into Embed"""
    embed: Embed
    """Embed made from this Entry"""
    source: 'Feed'
    """Source Feed from which this Entry comes from"""
    def __init__(self, entry: feedparser.FeedParserDict) -> None:
        self._entry = entry
        self.source = entry._feed
        self.make_embed()
        self.format(entry.get("description", entry.get("summary", "")))
    
    def get_processor(self) -> Callable:
        """Returns function responsible for processing text"""
        return processors.get(self.source.name, self.summarize)

    def format(self, description: str):
        """Formats description according to processor"""
        processor = self.get_processor()
        text = processor(description, self._entry.get('link'))
        additional_fields: list[Embed_Field] = []
        if text and type(text) is not str:
            additional_fields, text = text

        if len(text) <= Limits.DESCRIPTION:
            self.embed.setDescription(text)
        else:
            self.embed.addFields("\u200b", text)
        for field in additional_fields:
            self.embed.addField(field.name, field.value, field.inline)

    def preprocess(self):
        """Preprocess summary text. Shouldn't be needed once summarizes becomes default"""
        pass

    def summarize(self, description: str, url: str) -> str:
        """Summarizes post"""
        if self.source.fetch_content:
            # TODO: Fetch and parse content
            #description = newspaper_summary(self, url)
            pass
        soup = bs(description, "lxml")
        img = soup.find("img")
        if not self.embed.image.url and img and not img.get("src","").endswith("gif"):
            self.embed.image.url = img.get("src", "")
        description = toMarkdown(description).strip()
        import re
        image = RE_IMAGE_URL.search(description)
        description = RE_IMAGE_URL.sub(image.group(1) if image else "", description)
        description = re.split(rf'(Informacja|Artykuł|The post) \[?{re.escape(self.embed.title)}', description)[0]
        description = description.replace('Czytaj więcej...','').replace('Czytaj dalej','')

        return description.strip()

    def make_embed(self):
        """Creates embed from entry"""
        _ = self._entry
        images = filter(lambda x: 'image' in x.type, _.get('links', []))

        #FIXME
        image = next(images, None)
        if image:
            image = image.href
        thumbnail = next(images, None)
        if thumbnail:
            thumbnail = thumbnail.href
        author_avatar = None
        if author_avatar:
            author_avatar = author_avatar.href
        #TODO: Improve image detection

        self.embed = (
            Embed()
            .setUrl(_.get('link'))
            .setTimestamp(
                datetime.fromtimestamp(
                    time.mktime(
                        _.get('updated_parsed') or _.get('published_parsed')
                    ),
            )#tz=timezone.utc)
            )
            .setTitle(_.get('title'))
            .setImage(image)
            .setThumbnail(thumbnail)
            .setFooter(
                " ".join(
                    [_.get('author'), "@", (self.source.name or "SOURCE")]
                ) if _.get("author") else self.source.name, 
                author_avatar)
            .setColor(self.source.color)
        )


class SubscriptionGroup:
    """Embeds grouped for specific Thread"""
    embeds: List[Embed]
    """Embeds to send to this thread"""
    content: str
    """Content to include in message"""

    username: str
    """Username which should be used when sending this group"""
    avatar_url: str
    """Avatar which should be used when sending this group"""
    def __init__(self, webhook: 'Webhook', entries: List[Entry]) -> None:
        '''Filters embeds according to webhook subscriptions
        alongside other webhook specific data'''
        self.embeds = []
        self.content = ""
        self.username = None
        self.avatar_url = None

        for entry in filter(lambda x: any(x.source.name == sub.source for sub in webhook.subscriptions), entries):
            sub = next(filter(lambda x: x.source == entry.source.name, webhook.subscriptions), None)
            if sub.regex and not sub.search(entry.embed.description):
                continue
            if (sub.content or "") not in self.content:
                self.content += " "+sub.content
            if not self.username:
                self.username = sub.feed.name
            if not self.avatar_url:
                self.avatar_url = sub.feed.icon_url
            self.embeds.append(entry.embed)
        self.embeds.sort(key= lambda x: x.timestamp)


class Group:
    """Group of threads of embeds to be send to specific webhook"""
    threads: Dict[int, List[SubscriptionGroup]]
    """Threads with groupped embeds"""
    def __init__(self, webhook: 'Webhook', entries: List[Entry]) -> None:
        self.threads = {}
        from .models import Subscription
        for thread, thread_entries in groupby(sorted(entries, key=lambda x: x.source.name), key=lambda x: next(filter(lambda sub: x.source.name == sub.source, webhook.subscriptions), Subscription()).thread_id):
            sources = []
            for source, source_entries in groupby(thread_entries, key=lambda x: x.source.name):
                sources.append(SubscriptionGroup(webhook, list(source_entries)))
            self.threads[thread] = sources#SubscriptionGroup(webhook, list(thread_entries))
