#!/usr/bin/env python3.7
import helpers, database, builder, rss
from multiprocessing.dummy import Pool
pool = Pool(2)


db = database.Database()
def fetch(source):
    p = rss.Parser(db, source)
    p.entries()
    if p.embeds != []:
        return p.embeds
    return []

def main():
    sources = db.getSources()
    results_ = {}
    avatars = {}
    results_ = pool.map(fetch, sources)
    results_ = {sources[i][0]: x for i, x in enumerate(results_) if x != []}
    if results_ == {}:
        return
    for source in sources:
        avatars[source[0]] = source[5]
    webhooks = db.getWebhooks()
    for webhook in webhooks:
        results = results_
        embeds = []
        sources = sorted(webhooks[webhook], key=lambda w: w[2] or "", reverse=True)
        srcs = [s[0] for s in sources]
        content = ''
        filtered = []
        for source in sources:
            e_ = []
            if source[0] == 'all':
                for src in results:
                    if src not in srcs:
                        embeds += results[src]
            elif source[0] not in results:
                continue
            elif source[2] != '':
                filtered += helpers.filtr(results[source[0]], source[2])
                results[source[0]] = [embed for embed in results[source[0]] if embed not in filtered]
                src = source
                if filtered != []:
                    content += ' '+src[1]
            else:
                if len(results) <= 5:
                    _embeds = []
                    for src in sources:
                        if src[0] in results:
                                _embeds += results[src[0]]
                    sendEmbeds(_embeds, webhook)
                    break
                e_ += results[source[0]]
            if e_ != []:
                src = source
                sendEmbeds(e_, webhook, src[1], src[0], avatars[src[0]])
        if filtered != []:
            sendEmbeds(filtered, webhook, content, src[0], avatars[src[0]])
        if embeds != []:
            sendEmbeds(embeds, webhook)


from helpers import cumulative

def sendEmbeds(embeds, webhook, content='', username=None, avatar_url=None):
    total_characters = 0
    build = builder.Builder(content, username, avatar_url, [])
    for embed in embeds:
        total = cumulative(embed)
        if total_characters + total < 5500:
            total_characters += total
            build.addEmbed(embed)
        else:
            build.send_webhook(webhook)
            build = builder.Builder(content, username, avatar_url, [])
            build.addEmbed(embed)
            total_characters = cumulative(embed)
    if build.embeds != []:
        build.send_webhook(webhook)

        

#import time

#s = time.time()
main()
#e = time.time()
#print(e-s)