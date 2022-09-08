from datetime import timedelta
from MFramework import Groups, register, Context, Channel, Interaction
from models import Subscription, Webhook, Feed


async def Source(interaction: Interaction, user_input: str) -> list[str]:
    session = interaction._Client.db.sql.session()
    return [i[0] for i in session.query(Feed.name).filter(Feed.name.ilike(f"%{user_input}%")).limit(25).all()]


async def SubscribedSources(interaction: Interaction, user_input: str) -> list[str]:
    session = interaction._Client.db.sql.session()

    webhooks = filter(
        lambda x: x.user.id == interaction._Client.user_id,
        await interaction._Client.get_guild_webhooks(interaction.guild_id),
    )
    return [
        i[0]
        for i in session.query(Subscription.source)
        .filter(Subscription.webhook_id.in_([w.id for w in webhooks]), Subscription.source.ilike(f"%{user_input}%"))
        .limit(25)
        .all()
    ]


@register(group=Groups.ADMIN)
async def rss():
    """Management of RSS Subscriptions"""
    pass


@register(group=Groups.ADMIN, main=rss)
async def webhook():
    """Management of Webhook subscriptions"""
    pass


@register(group=Groups.ADMIN, main=webhook, private_response=True)
async def subscribe(ctx: Context, source: Source, regex: str, content: str, channel: Channel = None) -> str:
    """
    Subscribe webhook to an RSS
    Params
    ------
    source:
        Source you want to subscribe to.
    regex:
        Subscribe only if regex finds a match in entry's content.
    content:
        Message that should be sent with each webhook.
    webhook:
        Channel/Thread to use. Default is current one.
    """
    session = ctx.db.sql.session()

    webhooks = filter(lambda x: x.user.id == ctx.bot.user_id, await ctx.bot.get_guild_webhooks(ctx.guild_id))
    channel_webhook = next(filter(lambda x: x.channel_id == channel.id, webhooks))

    if not channel_webhook:
        channel_webhook = await ctx.bot.create_webhook(
            channel.id, source, feed.icon_url, f"RSS Subscribed by {ctx.user}"
        )
        webhook = Webhook(id=channel_webhook.id, token=channel_webhook.token)
        session.add(Webhook)

    if (
        session.query(Subscription)
        .filter(Subscription.feed.name == feed.name, Subscription.webhook_id == channel_webhook.id)
        .first()
    ):
        return f"{channel.name} is already subscribed to {feed.name}!"

    session.add(
        Subscription(
            webhook_id=webhook.id,
            source=source,
            regex=regex,
            content=content,
            thread_id=ctx.channel_id if ctx.data.is_thread else None,
        )
    )
    session.commit()

    return f"Subscribed to {feed.name} for {channel.name}!"


@register(group=Groups.ADMIN, main=webhook, private_response=True)
async def list(ctx: Context, channel: Channel = None) -> str:
    """
    Show subscribed sources alongside their channels for this server.
    Params
    ------
    channel:
        Channel subscribtions to show.
    """
    session = ctx.db.sql.session()
    webhooks = filter(
        lambda x: x.user.id == ctx.bot.user_id and ((channel and x.channel_id == channel) or True),
        await ctx.bot.get_guild_webhooks(ctx.guild_id),
    )
    subs = session.query(Subscription.source).filter(Subscription.webhook_id.in_([w.id for w in webhooks])).all()
    return "\n".join(
        [
            f"{k} - <#{v}>"
            for k, v in {sub.source: next(filter(lambda x: x.id == sub.id, subs).channel_id) for sub in subs}
        ]
    )


@register(group=Groups.ADMIN, main=webhook, private_response=True)
async def unsubscribe(ctx: Context, source: SubscribedSources) -> str:
    """
    Unsubscribe webhook from an RSS
    Params
    ------
    source:
        Source you want to unsubscribe from.
    """
    session = ctx.db.sql.session()

    webhooks = filter(lambda x: x.user.id == ctx.bot.user_id, await ctx.bot.get_guild_webhooks(ctx.guild_id))
    subscription = (
        session.query(Subscription)
        .filter(Subscription.webhook_id.in_([w.id for w in webhooks]), Subscription.source == source)
        .first()
    )

    if not subscription:
        return "This server is not subscribed to this source!"

    session.delete(subscription)
    session.commit()

    return f"Unsubscribed from {source} for {subscription.source}!"


@register(group=Groups.SYSTEM, main=rss)
async def feed():
    """RSS Feed management"""
    pass


@register(group=Groups.SYSTEM, main=feed)
async def add(
    ctx: Context,
    url: str,
    name: str = None,
    color: str = None,
    icon_url: str = None,
    fetch_content: bool = False,
    refresh_rate: timedelta = None,
):
    """
    Add new source
    Params
    ------
    url:
        URL of feed
    name:
        Feed's name
    color:
        Feed's color
    icon_url:
        URL of an icon
    fetch_content:
        Whether to fetch content
    refresh_Rate:
        Interval for feed fetching
    """
    session = ctx.db.sql.session()
    feed = session.query(Feed).filter(Feed.name == name).first()
    if feed:
        return f"Feed {feed.name} was already added"
    if not name:
        # TODO: get metadata from URL
        pass

    feed = Feed(name=name, url=url)
    feed.color = color
    feed.icon_url = icon_url
    feed.fetch_content = fetch_content
    feed.refresh_rate = refresh_rate
    session.add(feed)
    session.commit()
    return f"Added {feed.name} successfully"


@register(group=Groups.SYSTEM, main=feed)
async def remove(ctx: Context, feed: Source):
    """
    Remove feed from list
    Params
    ------
    feed:
        Feed to remove.
    """
    session = ctx.db.sql.session()
    feed = session.query(Feed).filter(Feed.name == feed).first()
    session.delete(feed)
    return f"Removed {feed.name} successfully"
