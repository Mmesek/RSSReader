import asyncio
import aiohttp, feedparser, pytz

from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from RSS.models import Feed_Post

from RSS.models import Feed
from RSS.utils import setup
from RSS.utils import log, get, parse_ts
from RSS.webhooks.__main__ import main as webhook


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

    tasks: list[asyncio.Task] = []
    entries: list["Feed_Post"] = []

    async with aiohttp.ClientSession() as client:
        for feed in _feeds:
            tasks.append(asyncio.create_task(fetch(feed, client), name=feed.name))

        for task in tasks:
            entries.extend(await task)

    for entry in entries:
        await entry.process()

    await webhook(session, entries)

    await session.commit()


async def fetch(feed: Feed, client: aiohttp.ClientSession) -> list["Feed_Post"]:
    """
    Get new entries since last fetch

    Params
    ------
    feed:
        Feed to fetch
    client:
        Aiohttp's Client Session for async HTTP requests
    """
    entries = []
    NOW = datetime.now(tz=timezone.utc)

    # Ensure ts has tz in an event where backend (SQLite) strips it away
    if not feed.timestamp.tzinfo:
        feed.timestamp = pytz.timezone("utc").localize(feed.timestamp)

    # Make sure refresh rate has already passed
    if feed.refresh_rate and feed.refresh_rate > NOW - feed.timestamp:
        log.info(
            "Skipping %s as refresh (%s) interval didn't pass since last post (%s) yet",
            feed.name,
            feed.refresh_rate,
            feed.timestamp,
        )
        return entries

    # Get feed with new entries
    result, status = await get(client, feed.url, modified=feed.timestamp.strftime("%a, %d %b %Y %H:%M:%S %Z"))

    # There are no new entries
    if status == 304:
        log.info("No new entries (Status code 304) on feed %s", feed.name)
        return entries

    _feed = feedparser.parse(result)
    _last_ts = feed.timestamp
    cutoff = NOW - timedelta(7)
    _skips = 0

    for entry in _feed["entries"]:
        _skip = False
        updated_ts = parse_ts(entry.get("updated", entry.get("published")))
        ts = parse_ts(entry["published"])
        # Make sure update is consistently AFTER publish
        updated_ts, ts = max(updated_ts, ts), min(updated_ts, ts)

        # Skip old entries
        if updated_ts < cutoff:
            continue

        # Ensure ts is in the past
        if updated_ts > NOW:
            updated_ts = NOW
        if ts > NOW:
            ts = NOW

        # If update was after last known ts, cache it
        if updated_ts > _last_ts:
            _last_ts = updated_ts

        # Skip entry if it's before last known post
        if updated_ts <= feed.timestamp:
            log.debug(
                "Skipping entry (%s) due to timestamp (%s) being before last post (%s)",
                entry.get("title", ""),
                ts,
                feed.timestamp,
            )
            _skips += 1
            _skip = True

        for _post in feed.posts:
            # Check if any existing post has same URL
            if _post.url == entry.get("link") and not _skip:
                # Update existing post
                log.debug("Detected same URL (%s). Updating existing post (%s)", _post.url, _post.title)
                post = _post
                post.updated_at = updated_ts
                post.summary = entry.get("summary", None)
                break
            # Check if any existing post has same title, author AND is within last 24h
            elif (
                _post.title == entry.get("title")
                and _post.author == entry.get("author", None)
                and _post.updated_at - updated_ts <= timedelta(1)
                and not _skip
            ):
                log.debug("Detected same title/author/timestamp combination (%s). Merging content", _post.title)
                # Merge with existing post
                if entry.get("description", "") not in _post.content:
                    _post.content += "\n\n" + entry.get("description", "")
                break
        else:
            # Create new post
            post = Feed_Post(
                url=entry.get("link"),
                title=entry.get("title"),
                content=entry.get("description", ""),
                summary=entry.get("summary", None),
                author=entry.get("author", None),
                thumbnail_url=entry.get(
                    "image",
                    entry.get("thumbnail", next(filter(lambda x: "image" in x.type, entry.get("links", [])), None)),
                ),
                timestamp=ts,
                updated_at=updated_ts,
                id=None,
                feed_id=feed.id,
                feed=feed,
                topic_analysis=None,
            )
            log.debug("Creating new post (%s)", post.title)

            entries.append(post)
            if feed.republish and not _skip:
                feed.posts.append(post)

    if _skips:
        log.info("Skipped %s old entries on feed %s", _skips, feed.name)

    # Ensure ts is in the past
    _ts = parse_ts(_feed["feed"]["updated"]) if "updated" in _feed["feed"] else _last_ts
    feed.timestamp = _ts if _ts < NOW else NOW

    if len(entries) - _skips:
        log.info("Got %s new entries from feed %s", len(entries) - _skips, feed.name)

    return entries


if __name__ == "__main__":
    db = asyncio.run(setup())

    asyncio.run(main(db.session()))
