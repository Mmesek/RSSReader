import argparse, functools, os, logging
from typing import Callable

import pytz, re
from aiohttp import ClientSession
from datetime import datetime
from dateutil import parser as dt_parser

from mlib.database import AsyncSQL
from mlib.config import ConfigToDict

log = logging.getLogger("RSS")

RE_IMAGE_URL = re.compile(r"\[?\!\[(.*?)\]\(\S*\)")

PROCESSORS: dict[str, list[Callable]] = {}
"""Registered Processors for RSS Sources"""

PRE_PROCESSORS: dict[str, list[Callable]] = {}
"""Registered Pre Processors (Cleaning) for RSS Entries"""

POST_PROCESSORS: dict[str, list[Callable]] = {}
"""Registered Post Processors (Summarizing, Extracting) for RSS Entries"""


def processor(cls: Callable = None, source: str = None, registry: dict[str, list[Callable]] = PROCESSORS):
    """Adds new processor to source"""

    @functools.wraps(cls)
    def inner(f: Callable):
        _name = source or f.__name__

        if _name not in registry:
            registry[_name] = []

        registry[_name].append(f)
        return f

    if cls:
        return inner(cls)
    return inner


def timed(func=None, msg: str = ""):
    """Logs execution time. First argument is length of result, then second is length of input argument. Delta is passed as last"""

    def inner(*args, **kwargs):
        import time

        start = time.perf_counter_ns()
        result = func(*args, **kwargs)
        finish = time.perf_counter_ns()

        log.info(msg, len(result), len(args[0]), finish - start)
        return result

    return inner


async def setup(*args):
    db = AsyncSQL(url="postgresql+psycopg://postgres:postgres@db/RSS")
    await db.create_tables()
    return db


async def _setup(parser: argparse.ArgumentParser) -> AsyncSQL:
    args = parser.parse_args()

    log.setLevel(args.log)

    if args.cfg:
        cfg = ConfigToDict(args.cfg)
        db = AsyncSQL(**cfg["Database"])
    else:
        try:
            url = os.getenv("DATABASE_URL")
        except AttributeError:
            log.critical("Connection string is not supplied!")
            url = None
        db = AsyncSQL(url=url, echo=False)

    await db.create_tables()
    return db


def parse_ts(timestamp: str) -> datetime:
    ts = dt_parser.parse(timestamp, tzinfos={"EET": 7200})
    if not ts.tzinfo:
        ts = pytz.timezone("utc").localize(ts)
    return ts


async def get(client: ClientSession, url: str, modified: str) -> tuple[str | None, int]:
    async with client.get(url, headers={"If-Modified-Since": modified}) as res:
        return await res.text() or None, res.status


async def send(client: ClientSession, url: str, json: dict) -> bool:
    async with client.post(url, json=json) as res:
        return res.status == 200
