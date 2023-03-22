import aiohttp
import asyncio
import time

from sqlalchemy.ext.asyncio import AsyncSession
from itertools import groupby

from RSS.models import Feed_Post
from RSS.utils import setup

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from RSS.utils import log

from .models import Webhook

from .formatters import discord


async def main(session: AsyncSession, posts: list[Feed_Post] = None):
    tasks: list[asyncio.Task] = []
    _start = time.perf_counter()

    async with aiohttp.ClientSession() as client:
        for webhook in await Webhook.get(session):
            if not posts:
                posts = await get_posts(session, webhook)

            # NOTE: Posts *could* be converted here and converted versions could be cached
            tasks.extend(group(webhook, posts, client))

        for task in tasks:
            await task

    log.info("Completed sending out %s webhook(s) in %s", len(tasks), _start - time.perf_counter())

    # Save changed timestamps
    await session.commit()


def group(webhook: Webhook, posts: list[Feed_Post], client: aiohttp.ClientSession) -> list[asyncio.Task]:
    """Creates async tasks sending posts to subscribing webhooks"""
    _tasks = []
    for feed_id, _posts in groupby(posts, key=lambda x: x.feed_id):
        # Get subscription for this feed
        if not (sub := next(filter(lambda x: x.feed_id == feed_id, webhook.subscriptions), None)):
            log.debug("Webhook %s is not subscribing to feed %s", webhook.id, sub.feed_id)
            continue

        # Filter posts for this subscription
        if _posts := list(
            filter(
                lambda x: x.feed_id == sub.feed_id
                and (x.timestamp > sub.timestamp if sub.only_new else Feed_Post.updated_at > sub.timestamp),
                _posts,
            )
        ):
            # Update last entry timestamp for subscription in webhook
            sub.timestamp = max([post.timestamp for post in _posts])

            # Convert and Send new entries
            # NOTE: Work duplication on convert step per webhook!
            log.info("Sending (%s) posts to subscription (%s) on feed %s", len(_posts), sub.id, sub.feed_id)
            _tasks.append(asyncio.create_task(sub.send(client, _posts)))
    return _tasks


async def get_posts(session: AsyncSession, webhook: Webhook) -> list[Feed_Post]:
    """Retrieves posts for each subscription of webhook that were fetched after last known sent post"""
    stmt = select(Feed_Post).options(selectinload(Feed_Post.feed))

    # Get all subscriptions with last sent entry
    for sub in webhook.subscriptions:
        stmt = stmt.where(
            Feed_Post.feed_id == sub.feed_id,
            Feed_Post.timestamp > sub.timestamp if sub.only_new else Feed_Post.updated_at > sub.timestamp,
        )

    r = await session.execute(stmt)
    posts = r.scalars().all()

    if posts:
        log.info("Got (%s) posts from database", len(posts))

    return posts


if __name__ == "__main__":
    db = asyncio.run(setup())

    asyncio.run(main(db.session()))
