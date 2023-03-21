from typing import Optional, Any, Callable
from datetime import datetime, timedelta

from sqlalchemy import select, func, ForeignKey, TIMESTAMP
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship as Relationship, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from mlib.database import ID, Timestamp, Base
from RSS.utils import log, PROCESSORS


def Field(foreign_key=None, **kwargs):
    return mapped_column(ForeignKey(foreign_key) if foreign_key else None, **kwargs)


class Feed(Timestamp, ID, Base):
    """RSS/Atom Feed Metadata"""

    name: Mapped[str]

    url: Mapped[str]
    """URL to fetch"""
    # last_post: Mapped[datetime]
    # """Last fetched post from this feed"""

    refresh_rate: Mapped[timedelta]
    """Rate at which RSS should be fetched"""

    language: Mapped[Optional[str]]
    """Language of this RSS"""
    icon_url: Mapped[Optional[str]]
    """Icon of source"""
    fetch_content: Mapped[Optional[bool]]
    """Whether full content of the post should be fetched
    or formatting should be performed using RSS-supplied text"""
    republish: Mapped[bool]
    """Whether post should be cached in a database"""
    color: Mapped[str]
    """Color of this feed. Generally theme color of a brand"""

    processors: list["Feed_Processor"] = Relationship("Feed_Processor", back_populates="feed")
    posts: list["Feed_Post"] = Relationship("Feed_Post", back_populates="feed")

    @classmethod
    def get_refreshed_stmt(cls):
        return (
            select(cls)
            .where(func.now() - cls.timestamp > cls.refresh_rate)
            .options(selectinload(cls.posts), selectinload(cls.processors))
        )

    @classmethod
    async def get(cls, session: AsyncSession, feeds: list[str]) -> list["Feed"]:
        """Retrieves feeds for which refresh rate is already new from Database"""
        stmt = cls.get_refreshed_stmt()
        if feeds:
            stmt = stmt.where(cls.name.in_(feeds))

        f = await session.execute(stmt)
        f = f.scalars().all()
        log.info("Got (%s) feed sources from database", len(f))
        return f

    @classmethod
    def sync_get(cls, session: Session, feeds: list[str]) -> list["Feed"]:
        """Retrieves feeds for which refresh rate is already new from Database"""
        stmt = cls.get_refreshed_stmt
        if feeds:
            stmt = stmt.where(cls.name.in_(feeds))

        f = session.execute(stmt).scalars().all()
        log.info("Got (%s) feed sources from database", len(f))
        return f


class Feed_Processor(ID, Base):
    """Processing logic for this feed"""

    name: Mapped[str]

    feed_id: Mapped[int] = Field(foreign_key="Feed.id")
    """ID of related Feed"""
    feed: Feed = Relationship("Feed")

    value: Mapped[str]
    """Value passed to Processor. 
    Can be anything processor uses like search term, cutoff etc
    """
    order: Mapped[int]
    """Order in which processor should be run"""

    async def run(self, post: "Feed_Post", processors: dict[list[str, Callable]] = PROCESSORS) -> bool:
        results = set()
        for proc in processors.get(self.name):
            results.add(await proc(post, self.value))
        return any(results)


class Feed_Post(Timestamp, ID, Base):
    feed_id: Mapped[int] = Field(foreign_key="Feed.id")
    """ID of related Feed"""
    feed: Optional[Feed] = Relationship("Feed")

    title: Mapped[str]
    """Title of this post"""
    content: Mapped[str]
    """Post content"""
    url: Mapped[str]
    """Source URL to Post"""
    summary: Mapped[Optional[str]]
    """Summary of Post"""

    author: Mapped[Optional[str]]
    """Author of Post"""
    thumbnail_url: Mapped[Optional[str]]
    """URL to Post's Thumbnail"""
    updated_at: Mapped[Optional[datetime]] = Field(TIMESTAMP(timezone=True), server_default=func.now())
    """Timestamp when Post was updated"""
    # tags: Mapped[list[str]]
    """Tags used in this post"""
    topic_analysis: Any
    """Post's Topics"""

    async def process(self) -> None:
        for processor in sorted(self.feed.processors, key=lambda x: x.order):
            if await processor.run(self):
                return

    @property
    def total_characters(self) -> int:
        return sum(len(i) for i in [self.content or self.summary, self.author, self.title])
