import re
from datetime import datetime, timedelta, timezone
from typing import List, Set

import feedparser
from dateutil import parser as dt_parser
from mdiscord.models import Embed, Limits

import sqlalchemy as sa
from sqlalchemy.orm import relationship
from mlib.database import Base

from mdiscord.http_client import HTTP_Client as RESTClient

from .utils import Group

class FeedMeta:
    """Feed Metadata used mainly to pass data around"""
    name: str = sa.Column(sa.String, primary_key=True)
    '''Name of the RSS source'''
    language: str = sa.Column(sa.String)
    '''Language of this RSS'''
    icon_url: str = sa.Column(sa.String)
    '''Avatar used in a Webhook'''
    color: str = sa.Column(sa.String)
    '''Color of embed'''
    fetch_content: bool = sa.Column(sa.Boolean, default=True)
    """Whether full content of the news should be fetched
    or formatting should be performed using RSS-supplied text"""

    def __init__(self, name: str, color: str, icon: str, language: str, fetch: bool) -> None:
        self.name: str = name
        self.language: str = language
        self.icon_url: str = icon
        self.color: str = color
        self.fetch_content: bool = fetch

class Feed(FeedMeta, Base):
    """RSS/Atom Feed Metadata"""
    url: str = sa.Column(sa.String)
    '''URL to fetch'''
    last_post: datetime = sa.Column(sa.DateTime(True))
    """Last fetched post from this feed"""

    refresh_rate: timedelta = sa.Column(sa.Interval, default=timedelta())
    '''Rate at which RSS should be fetched'''

    components: List['Feed_Component'] = relationship("Feed_Component", back_populates="feed", foreign_keys="Feed_Component.source")

    def __init__(self, name: str, url: str, last_post: datetime = None) -> None:
        self.name: str = name
        self.url: str = url
        self.last_post: datetime = last_post or datetime.now(timezone.utc)
    
    def get_new(self) -> Set[feedparser.FeedParserDict]:
        """Get new entries since last fetch"""
        entries = set()
        _last_post = self.last_post

        if not self.last_post.tzinfo:
            #HACK for sqlite
            import pytz
            self.last_post = pytz.timezone("utc").localize(self.last_post)

        if self.refresh_rate and self.refresh_rate > datetime.now(tz=timezone.utc) - self.last_post:
            return entries

        _feed = feedparser.parse(self.url, modified=self.last_post)

        if _feed.get('status') == 304:
            return entries

        for entry in _feed.entries:
            try:
                _ts = entry.updated
            except:
                _ts = entry.published
            ts = dt_parser.parse(_ts, tzinfos={"EET":7200})
            if not ts.tzinfo:
                import pytz
                ts = pytz.timezone("utc").localize(ts)

            if ts > _last_post:
                _last_post = ts
            elif ts <= self.last_post:
                continue

            entry._feed = self#FeedMeta(self.name, self.color, self.icon_url, self.language, self.fetch_content)
            entries.add(entry)
        self.last_post = _last_post

        return entries
    
    @classmethod
    def get(cls, session: sa.orm.Session) -> List['Feed']:
        """Retrieves feeds from Database"""
        return (
            session.query(cls)
            .filter(
                sa.func.now()-cls.last_post > cls.refresh_rate #Possibly FIXME?
            )
            .all()
        )

class Feed_Component(Base):
    name: str = sa.Column(sa.String, primary_key=True)
    source: str = sa.Column(sa.ForeignKey("Feed.name"), primary_key=True)
    feed: Feed = relationship("Feed")
    value: str = sa.Column(sa.String)


class Subscription(Base):
    """Webhook's subscription to Feed"""
    webhook_id: int = sa.Column(sa.ForeignKey("Webhook.id"), primary_key=True)
    """ID of webhook this subscription is for"""
    webhook: 'Webhook' = relationship("Webhook")
    """Associated Webhook object"""
    source: str = sa.Column(sa.ForeignKey("Feed.name"), primary_key=True)
    """Source to which this subscription is for"""
    feed: Feed = relationship("Feed")
    """Associated Feed object"""
    regex: re.Pattern = sa.Column(sa.String, primary_key=True, default="")
    # Sadly regex is in fact a str
    """Regular expression that should be applied on entry's content"""
    content: str = sa.Column(sa.String)
    """Content that should be sent alongside embed for this subscription"""
    thread_id: int = sa.Column(sa.BigInteger)
    """ID of a Thread to which embed should be sent to"""
 
    _compiled_regex: re.Pattern = None
    """Compiled regex pattern"""
    #TODO: Actually, check if it's possible to compile it into `regex` member variable directly to skip that indirection
 
    def search(self, string: str) -> re.Match:
        """Compiles regex if not compiled already and searches provided string for a match"""
        if not self._compiled_regex:
            self._compiled_regex = re.compile(self.regex)
        return self._compiled_regex.search(string)


class Webhook(Base):
    """Webhook metadata"""
    id: int = sa.Column(sa.BigInteger, primary_key=True)
    """ID of this Webhook"""
    token: str = sa.Column(sa.String)
    """Token of this Webhook"""

    subscriptions: List[Subscription] = relationship("Subscription", back_populates="webhook", foreign_keys="Subscription.webhook_id")
    """Subscriptions for this Webhook"""

    async def _send(self, client: RESTClient, thread: int, group: Group, embeds: List[Embed]):
        """Wrapper around webhook execute"""
        if not group.content and not embeds:
            return
        await client.execute_webhook(
            self.id, self.token, thread_id=thread, 
            content=group.content, 
            username=group.username, avatar_url=group.avatar_url, embeds=embeds, 
            allowed_mentions=None
        )#[i for i in embeds if i])

    async def send(self, client: RESTClient, formatted_entries: list) -> None:
        '''Sends Embeds in groups by source (up to 10 at once) below total embed's character limit using this webhook'''
        _group = Group(self, formatted_entries)
        for thread, groups in _group.threads.items():
            for group in groups:
                _embeds = []
                #from mlib.utils import grouper
                #for embeds in grouper(group.embeds, 5):
                for embed in group.embeds:
                    if embed.total_characters + sum(i.total_characters for i in _embeds) < Limits.TOTAL and len(_embeds) < 10:
                        _embeds.append(embed)
                    else:
                        await self._send(client, thread, group, _embeds)
                        _embeds = []
                if _embeds:
                    await self._send(client, thread, group, _embeds)

    @classmethod
    def get(cls, session: sa.orm.Session) -> List['Webhook']:
        """Retrieves webhooks from Database"""
        return session.query(cls).all()
