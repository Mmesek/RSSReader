import asyncio, time
from typing import List
from multiprocessing import dummy

import sqlalchemy as sa

from mdiscord.http_client import HTTP_Client as RESTClient

from mlib.database import SQL
from mlib.config import ConfigToDict
from mlib.logger import log

from .models import Feed, Webhook
from .utils import Entry, processors as components
from . import processors # noqa: F401

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--database", help="Path to database", default="localhost")
parser.add_argument("--name", help="Name of database", default="RSS")
parser.add_argument("feeds", nargs="*", help="List of feeds to fetch")
parser.add_argument("--webhook", help="Webhook id and token (id/token) to which feeds should be sent to")
parser.add_argument("--cfg", help="Path to config file", default="config.ini")


async def main(session: sa.orm.Session, client: RESTClient = None, feeds: List[Feed] = None, webhooks: List[Webhook] = None) -> None:
    """
    Main RSS logic function.
    - Fetches feeds from database
    - Retrieves articles
    - Saves last article date to database
    - Parses Entries into Embeds
    - Fetches webhooks from database
    - Sends webhooks accordingly to subscriptions & threads

    Params
    ------
    session:
        Session to use for database transactions
    client:
        Discord's REST Client to use for sending webhooks
    feeds:
        Overwrite for feeds to fetch (skips database fetch)
    webhooks:
        Overwrite for webhooks to use (skips database fetch)
    """
    feeds = feeds or Feed.get(session)

    _s = time.time()

    with dummy.Pool() as pool:
        r = pool.map(lambda x: x.get_new(), feeds)
        session.commit()
        _f = time.time()
        log.info("Fetched new (%s) from feeds (%s) in %s", len([i for i in r if i]), len(r), _f - _s)

        _ = []
        list(map(_.extend, r))

        entries: set[Entry] = set(pool.map(Entry, _))
    _p = time.time()
    log.info("Entries (%s) created & parsed in %s", len(entries), _p - _f)

    for entry in entries.copy():
        for component in entry.source.components:
            if not components.get(component.name, lambda x, y: (True))(entry, component.value):
                entries.remove(entry)
                break

    _filtered = time.time()
    log.info("Entries (%s) filtered in %s", len(entries), _filtered - _p)

    webhooks = webhooks or Webhook.get(session)

    client = client or RESTClient()

    for webhook in webhooks:
        await webhook.send(client, entries)

    log.info("Sent to (%s) webhooks in %s", len(webhooks), time.time() - _filtered)

    await client.close()
    return

if __name__ == '__main__':
    args = parser.parse_args()
    if args.cfg:
        cfg = ConfigToDict(args.cfg)
        db = SQL(**cfg['Database'])
    else:
        db = SQL(db="sqlite", name="RSS", echo=False)

    db.create_tables()
    session = db.session()

    asyncio.run(main(session))
