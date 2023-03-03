from datetime import datetime, timedelta
from html import escape

from aiohttp import web
from sqlalchemy import select

from mlib.database import AsyncSQL

from RSS.utils import parse_ts
from RSS.models import Feed_Post, Feed

from .feed_generator import Atom_Generator, Atom_Item, RSS_Generator, RSS_Item

parser = argparse.ArgumentParser()

routes = web.RouteTableDef()

h = h2t()


async def get_posts(request: web.Request):
    modified_since = request.headers.get("if-modified-since", None)
    if modified_since:
        modified_since = parse_ts(modified_since)

    async with db.session() as session:
        stmt = (
            select(Feed_Post)
            .where(
                Feed_Post.feed_id.in_([1, 2, 3, 4, 5]),
                Feed_Post.timestamp > (modified_since or datetime.now() - timedelta(days=7)),
            )
            .order_by(Feed_Post.timestamp.desc())
        )
        result = await session.execute(stmt)
        posts: list[Feed_Post] = result.scalars().all()

    return posts


def build_response(feed: Atom_Generator | RSS_Generator, items: list[Atom_Item | RSS_Item]) -> web.Response:
    built = feed.build(items)

    return web.Response(
        text=built,
        content_type="text/xml",
        headers={"Last-Modified": getattr(feed, "updated", getattr(feed, "pubDate", None))},
        status=304 if not len(items) else 200,
    )


@routes.get("/feed")
async def feed(request: web.Request):
    items = []
    for post in await get_posts(request):
        new_author = post.title.split("@")[-1].strip()
        new_author = new_author if new_author != post.title else post.author
        if new_author:
            post.author = "<name>" + escape(new_author) + "</name>"
        post.title = escape("@".join(post.title.split("@")[:-1]).strip() or post.title)
        items.append(Atom_Item.from_feed_post(post))

    _feed = Atom_Generator("Feed", "http://localhost:8080/feed", "feed", None, "mRSS")
    return build_response(_feed, items)


@routes.get("/rss")
async def rss(request: web.Request):
    items = []
    for post in await get_posts(request):
        new_author = post.title.split("@")[-1].strip()
        new_author = new_author if new_author != post.title else post.author
        if new_author:
            post.author = escape(new_author)
        post.title = escape("@".join(post.title.split("@")[:-1]).strip() or post.title)
        items.append(RSS_Item.from_feed_post(post))

    _feed = RSS_Generator("RSS", "http://localhost:8080/rss", generator="mRSS")
    return build_response(_feed, items)


@routes.post("/new")
async def new(request: web.Request):
    req = await request.json()
    async with db.session() as session:
        session.add(
            Feed(
                name=req.get("name"),
                url=req.get("url"),
                refresh_rate=timedelta(),
                timestamp=datetime.now() - timedelta(1),
                id=None,
                language=req.get("language", "en"),
                icon_url=None,
                fetch_content=None,
                processors=[],
                posts=[],
            )
        )
        await session.commit()
    return web.Response()


db = AsyncSQL(url="postgresql+psycopg://postgres:postgres@r4/sa2")  # setup(parser)


def run():
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)


if __name__ == "__main__":
    run()
