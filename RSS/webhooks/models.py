import re
import aiohttp

from sqlalchemy import select
from sqlalchemy.orm import Mapped, relationship as Relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from RSS.utils import log, send
from RSS.models import ID, Timestamp, Feed, Field, Base, Feed_Post

from .formatters import LIMITS, REQUESTS


class Subscription(Timestamp, Base):
    """Webhook's subscription to Feed"""

    id: Mapped[int] = Field(foreign_key="Webhook.id", primary_key=True)
    """ID of webhook this subscription is for"""
    webhook: "Webhook" = Relationship("Webhook")
    """Associated Webhook object"""

    feed_id: Mapped[str] = Field(foreign_key="Feed.id", primary_key=True)
    """Source to which this subscription is for"""
    feed: Feed = Relationship("Feed")
    """Associated Feed object"""

    content: Mapped[str] = None
    """Content that should be sent alongside embed for this subscription"""

    _compiled_regex: re.Pattern = None
    """Compiled regex pattern"""

    _compiled_blacklist: re.Pattern = None
    """Compiled blacklist regex pattern"""

    regex: Mapped[str] = Field(primary_key=True, default="")
    """Regular expression that should be applied on entry's content"""

    regex_blacklist: Mapped[str] = Field(primary_key=True, default="")
    """Regular expression that should be skip if found on entry's content"""

    only_new: Mapped[bool] = Field(default=False)
    """Whether to only send new entries or also include updated ones"""

    def search(self, string: str) -> re.Match:
        """Compiles regex if not compiled already and searches provided string for a match"""
        if not self._compiled_regex:
            log.debug("Compiling regex %s", self.regex)
            self._compiled_regex = re.compile(self.regex)

        log.debug("Searching for Match by Regex %s", self.regex)
        return self._compiled_regex.search(string)

    def check_blacklist(self, string: str) -> re.Match:
        """Compiles regex if not compiled already and searches provided string for a match"""
        if not self._compiled_blacklist:
            log.debug("Compiling regex %s", self.regex_blacklist)
            self._compiled_blacklist = re.compile(self.regex_blacklist)

        log.debug("Searching for Blacklist by Regex %s", self.regex_blacklist)
        return self._compiled_blacklist.search(string)

    async def send(self, client: aiohttp.ClientSession, posts: list[Feed_Post]):
        entries: list[Feed_Post] = []
        posts.sort(key=lambda x: x.timestamp)
        request = REQUESTS[self.webhook.platform]

        # Send only entries that match regex (if there is regex)
        for post in filter(
            lambda x: not self.regex
            or (self.search(x.title) or self.search(x.content or x.summary))
            and not self.regex_blacklist
            or not self.check_blacklist(x.title),
            posts,
        ):
            # Group together entries with respect to platform limits
            if (
                post.total_characters + sum(i.total_characters for i in entries)
                < LIMITS.get(self.webhook.platform).TOTAL
                and len(entries) < LIMITS.get(self.webhook.platform).EMBEDS
            ):
                entries.append(post)
            else:
                # Send current group if next entry exceeeds limits
                log.debug("Sending (%s) entries to webhook %s", len(entries), self.feed.name)
                await send(client, self.webhook.url, json=request(self, entries).as_dict())
                entries = []

        if entries:
            # Send any remaining entries
            log.debug("Sending (%s) entries to webhook %s", len(entries), self.feed.name)
            await send(client, self.webhook.url, json=request(self, entries).as_dict())


class Webhook(ID, Base):
    """Webhook metadata"""

    url: Mapped[str]
    """URL to this Webhook"""

    subscriptions: list[Subscription] = Relationship("Subscription", back_populates="webhook")
    """Subscriptions for this Webhook"""

    @property
    def platform(self) -> str:
        """Extracts domain out of webhook's URL as platform name"""
        return self.url.split("/")[2].split(".")[-2].lower()

    @classmethod
    async def get(cls, session: AsyncSession) -> list["Webhook"]:
        """Retrieves webhooks from Database"""
        stmt = select(cls).options(selectinload(cls.subscriptions))
        w = await session.execute(stmt)
        w = w.scalars().all()

        # NOTE: Somehow this fixes lazyloading when accessing Subscription.webhook
        for _ in w:
            for s in _.subscriptions:
                hasattr(s, "webhook")

        log.info("Got (%s) webhooks from database", len(w))
        return w
