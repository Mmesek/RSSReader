from datetime import datetime, UTC
from dataclasses import dataclass
from RSS.models import Feed_Post
import pytz


@dataclass
class Tree:
    # title: str
    # link: str

    def build(self) -> str:
        item = ""
        for attribute in self.__annotations__:
            if self.__dict__[attribute]:
                item += f"\n<{attribute}>{self.__dict__[attribute]}</{attribute}>\n"

        return item


@dataclass
class Atom_Generator(Tree):
    title: str
    link: str
    id: str
    updated: datetime
    author: str  # Special
    category: str = None  # Special
    contributor: str = None  # Special
    generator: str = "mRSS"  # Special
    icon: str = None
    logo: str = None
    rights: str = None
    subtitle: str = None

    def build(self, items: list["Atom_Item"]) -> str:
        ts = None

        for item in items:
            if not ts or ts < item.updated:
                ts = item.updated

        if ts:
            if not ts.tzinfo:
                ts = pytz.timezone("utc").localize(ts)
            self.updated = ts.isoformat() if ts <= datetime.now(tz=UTC) else datetime.now(tz=UTC).isoformat()
        else:
            self.updated = datetime.now().isoformat()

        items = "\n".join([i.build() for i in items])
        return f'<?xml version="1.0" encoding="utf-8"?>\n<feed xmlns="http://www.w3.org/2005/Atom">{super().build()}\n{items}\n</feed>'


@dataclass
class Atom_Item(Tree):
    title: str
    link: str
    id: str = None
    updated: datetime = None
    summary: str = None
    author: str = None  # Special
    content: str = None
    link: str = None
    category: str = None  # Special
    contributor: str = None  # special
    published: datetime = None
    rights: str = None  # Special
    source: str = None  # Special

    def build(self) -> str:
        if self.published:
            if not self.published.tzinfo:
                self.published = pytz.timezone("utc").localize(self.published)
            self.published = (
                self.published.isoformat()
                if self.published <= datetime.now(tz=UTC)
                else datetime.now(tz=UTC).isoformat()
            )
        if self.updated:
            if not self.updated.tzinfo:
                self.updated = pytz.timezone("utc").localize(self.updated)
            self.updated = (
                self.updated.isoformat() if self.updated <= datetime.now(tz=UTC) else datetime.now(tz=UTC).isoformat()
            )
        link = f'<link rel="alternate" href="{self.link}"/>'
        self.link = None
        return "<entry>" + link + super().build() + "</entry>"

    @classmethod
    def from_feed_post(cls, post: Feed_Post):
        return cls(
            title=getattr(post, "title", "").strip(),
            link=post.url.strip(),
            id=post.url.strip(),
            updated=post.updated_at or post.timestamp,
            summary=getattr(post, "summary", "").strip(),
            author=getattr(post, "author", "").strip(),
            content=getattr(post, "content", "").strip(),
            published=post.timestamp,
        )


@dataclass
class RSS_Generator(Tree):
    title: str
    link: str
    description: str = None
    pubDate: str = None
    lastBuildDate: str = None
    docs: str = None
    managingEditor: str = None
    webMaster: str = None
    generator: str = "mRSS"
    language: str = "en-US"
    copyright: str = None
    ttl: int = None
    rating: str = None
    category: str = None  # Special
    cloud: str = None  # Special
    image: str = None  # Special
    textInput: str = None  # Special
    skipHours: str = None  # Special
    skipDays: str = None  # Special

    def build(self, items: list["RSS_Item"]) -> str:
        ts = None

        for item in items:
            if not ts or ts < item.pubDate:
                ts = item.pubDate

        ts = ts.strftime("%a, %d %b %Y %H:%M:%S %Z" + "GMT")
        self.pubDate = ts
        self.lastBuildDate = ts

        items = "\n".join([i.build() for i in items])
        return f'<rss version="2.0"><channel>{super().build()}{items}</channel></rss>'


@dataclass
class RSS_Item(Tree):
    title: str
    link: str
    description: str
    author: str
    pubDate: datetime = None
    guid: str = None  # Can have attribute
    category: str = None  # Special
    comments: str = None
    enclosure: str = None  # Special
    source: str = None

    def build(self) -> str:
        if self.pubDate:
            self.pubDate = self.pubDate.strftime("%a, %d %b %Y %H:%M:%S %Z" + "GMT")
        return f"<item>{super().build()}</item>"

    @classmethod
    def from_feed_post(cls, post: Feed_Post):
        return cls(
            title=getattr(post, "title", "").strip(),
            link=post.url.strip(),
            description=getattr(post, "content", "").strip(),
            author=getattr(post, "author", "").strip(),
            pubDate=post.updated_at or post.timestamp,
            guid=post.url.strip(),
        )
