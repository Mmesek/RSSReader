import asyncio, argparse
import aiohttp
import feedparser
import aiohttp
import pytz
from datetime import datetime, timedelta, timezone

from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from RSS.models import Feed_Post

from RSS.models import Feed
from RSS.utils import setup
from RSS.utils import log, get, parse_ts

parser = argparse.ArgumentParser()
parser.add_argument("--database", help="Path to database", default="localhost")
parser.add_argument("--name", help="Name of database", default="RSS")
parser.add_argument("feeds", nargs="*", help="List of feeds to fetch")
parser.add_argument("--log", default="WARNING", help="Specifies logging level", choices=["DEBUG", "INFO", "WARNING"])


async def main(session: AsyncSession, feeds: list[str] = None) -> None:
    """
    Main RSS logic function.
    - Fetches feeds from database
    - Retrieves articles
    - Saves articles to database

    Params
    ------
    session:
        Session to use for database transactions
    feeds:
        Overwrite for feeds to fetch
    """
    _feeds: list[Feed] = await Feed.get(session, feeds)
    entries = await fetch(_feeds, session)

    tasks: list[asyncio.Task] = []
    entries: list["Feed_Post"] = []

    async with aiohttp.ClientSession() as client:
        for feed in _feeds:
            tasks.append(asyncio.create_task(feed.fetch(client), name=feed.name))

        for task in tasks:
            entries.extend(await task)

    for entry in entries:
        await entry.process()

    await session.commit()


# @timed(msg="Fetched %s new entries from %s feed(s) in %s")
async def fetch(feed: Feed, client: aiohttp.ClientSession) -> list["Feed_Post"]:
    """Get new entries since last fetch"""
    entries = []

    if not feed.timestamp.tzinfo:
        feed.timestamp = pytz.timezone("utc").localize(feed.timestamp)

    if feed.refresh_rate and feed.refresh_rate > datetime.now(tz=timezone.utc) - feed.timestamp:
        log.debug(
            "Skipping %s as refresh rate (%s) interval didn't elapse since last post (%s) yet",
            feed.name,
            feed.refresh_rate,
            feed.timestamp,
        )
        return entries

    result, status = await get(client, feed.url, modified=feed.timestamp.strftime("%a, %d %b %Y %H:%M:%S %Z"))

    if status == 304:
        log.debug("No new entries (Status code 304) on feed %s", feed.name)
        return entries

    _feed = feedparser.parse(result)

    _last_ts = feed.timestamp

    now = datetime.now(tz=timezone.utc)
    cutoff = now - timedelta(7)
    for entry in _feed["entries"]:
        updated_ts = parse_ts(entry.get("updated", entry.get("published")))
        ts = parse_ts(entry["published"])

        updated_ts, ts = max(updated_ts, ts), min(updated_ts, ts)
        if updated_ts < cutoff:
            continue

        if updated_ts > now:
            updated_ts = now
        if ts > now:
            ts = now

        if updated_ts > _last_ts:
            _last_ts = updated_ts

        if ts <= feed.timestamp:
            log.debug(
                "Skipping entry (%s) due to timestamp (%s) being before last post (%s)",
                entry.get("title", ""),
                ts,
                feed.timestamp,
            )
            continue

        for _post in feed.posts:
            if _post.url == entry.get("link"):
                post = _post
                post.updated_at = updated_ts
                post.summary = entry.get("summary", None)
                break
        else:
            post = Feed_Post(
                url=entry.get("link"),
                title=entry.get("title"),
                content=entry.get("description", ""),
                summary=entry.get("summary", None),
                author=entry.get("author", None),
                thumbnail_url=entry.get("image", None),
                timestamp=ts,
                updated_at=updated_ts,
                id=None,
                feed_id=None,
                feed=None,
                topic_analysis=None,
            )

            for _post in feed.posts:
                if (
                    post.title == _post.title
                    and post.author == _post.author
                    and post.timestamp - _post.timestamp <= timedelta(1)
                ):
                    if post.content not in _post.content:
                        _post.content += "\n\n" + post.content
                    break
            else:
                entries.append(post)
                feed.posts.append(post)

    _ts = parse_ts(_feed["feed"]["updated"]) if "updated" in _feed["feed"] else _last_ts
    if _ts > now:
        _ts = now

    feed.timestamp = _ts

    log.debug("Got %s new entries from feed %s", len(entries), feed.name)
    return entries


if __name__ == "__main__":
    db = asyncio.run(setup(parser))

    asyncio.run(main(db.session()))
