#!/usr/bin/env python3.7
import helpers, database, builder, rss
from multiprocessing.dummy import Pool
pool = Pool(2)
import copy

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
        results = copy.deepcopy(results_)
        embeds = []
        sources = sorted(webhooks[webhook], key=lambda w: w[2] or "", reverse=True)
        srcs = [s[0] for s in sources]
        content = ''
        filtered = []
        filtered_src = []
        for source in sources:
            e_ = []
            if source[0] == 'all':
                for src in results:
                    if src not in srcs:
                        embeds += results[src]
            elif source[0] not in results:
                continue
            elif source[2] != '':
                f_ = []
                f_ += helpers.filtr(results[source[0]], source[2])
                src = source
                if f_ != []:
                    content += ' ' + src[1]
                filtered += f_
                filtered_src.append(src[0])
                results[source[0]] = [embed for embed in results[source[0]] if embed not in filtered]
            else:
                if len(results) <= 5:
                    _embeds = []
                    for src in sources:
                        if src[0] in results:
                                _embeds += results[src[0]]
                    sendEmbeds(_embeds, webhook, '', None, None)
                    break
                e_ += results[source[0]]
            if e_ != []:
                src = source
                sendEmbeds(e_, webhook, src[1], src[0], avatars[src[0]])
        if filtered != []:
            sendEmbeds(filtered, webhook, content, filtered_src[0], avatars[filtered_src[0]])
        if embeds != []:
            sendEmbeds(embeds, webhook, '', None, None)


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