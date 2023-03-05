import aiohttp
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from itertools import groupby

from RSS.models import Feed_Post
from RSS.utils import setup

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .models import Webhook

from .formatters import discord


async def main(session: AsyncSession):
    tasks: list[asyncio.Task] = []

    async with aiohttp.ClientSession() as client:
        for webhook in await Webhook.get(session):
            posts = await get_posts(session, webhook)

            # NOTE: Posts *could* be converted here and converted versions could be cached
            if task := group(webhook, posts, client):
                tasks.append(task)

        for task in tasks:
            await task

    # Save changed timestamps
    await session.commit()


def group(webhook: Webhook, posts: list[Feed_Post], client: aiohttp.ClientSession) -> asyncio.Task:
    """Creates async tasks sending posts to subscribing webhooks"""
    for feed_id, _posts in groupby(posts, key=lambda x: x.feed_id):
        # Get subscription for this feed
        if not (sub := next(filter(lambda x: x.feed_id == feed_id, webhook.subscriptions), None)):
            continue

        # Filter posts for this subscription
        if _posts := list(filter(lambda x: x.feed_id == sub.feed_id and x.timestamp > sub.timestamp, _posts)):
            # Update last entry timestamp for subscription in webhook
            sub.timestamp = max([post.timestamp for post in _posts])

            # Convert and Send new entries
            # NOTE: Work duplication on convert step per webhook!
            return asyncio.create_task(sub.send(client, _posts))


async def get_posts(session: AsyncSession, webhook: Webhook) -> list[Feed_Post]:
    """Retrieves posts for each subscription of webhook that were fetched after last known sent post"""
    stmt = select(Feed_Post).options(selectinload(Feed_Post.feed))

    # Get all subscriptions with last sent entry
    for (feed_id, timestamp) in [(s.feed_id, s.timestamp) for s in webhook.subscriptions]:
        stmt = stmt.where(Feed_Post.feed_id == feed_id, Feed_Post.timestamp > timestamp)

    r = await session.execute(stmt)
    return r.scalars().all()


if __name__ == "__main__":
    db = asyncio.run(setup())

    asyncio.run(main(db.session()))
