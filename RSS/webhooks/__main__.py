import aiohttp
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession
from itertools import groupby

from RSS.models import Feed_Post
from RSS.utils import setup

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .models import Webhook


async def main(session: AsyncSession):
    # Get all webhooks
    webhooks = await Webhook.get(session)
    tasks: list[asyncio.Task] = []

    async with aiohttp.ClientSession() as client:
        for webhook in webhooks:
            # Get all subscriptions with last sent entry
            subs = [(s.feed_id, s.timestamp) for s in webhook.subscriptions]
            stmt = select(Feed_Post).options(selectinload(Feed_Post.feed))

            for sub in subs:
                stmt = stmt.where(Feed_Post.feed_id == sub[0], Feed_Post.timestamp > sub[1])

            r = await session.execute(stmt)
            posts: list[Feed_Post] = r.scalars().all()
            # NOTE: Posts *could* be converted here and converted versions could be cached

            for feed_id, _posts in groupby(posts, key=lambda x: x.feed_id):
                for sub in webhook.subscriptions:
                    if sub.feed_id == feed_id:
                        # Update last entry timestamp for each subscription in webhook
                        sub.timestamp = max([post.timestamp for post in _posts])
                        break

                # Convert and Send new entries
                # NOTE: Work duplication on convert step per webhook!
                tasks.append(asyncio.create_task(sub.send(client, _posts)))

        for task in tasks:
            await task

    # Save changed timestamps
    await session.commit()


if __name__ == "__main__":
    db = asyncio.run(setup())

    asyncio.run(main(db.session()))
