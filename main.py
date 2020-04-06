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
    for source in sources:
    #    p = rss.Parser(db, source)
    #    p.entries()
    #    if p.embeds != []:
    #        results_[source[0]] = p.embeds
        avatars[source[0]] = source[5]
    if results_ == {}:
        return
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
                    #build = builder.Builder(src[1], src[0], avatars[src[0]], embeds=filtered)
                    #build.send_webhook(webhook)
            else:
                build = builder.Builder()
                if len(results) <= 5:
                    build.embeds = []
                    for src in sources:
                        if src[0] in results:
                            if len(build.embeds) < 10:
                                build.addEmbeds(results[src[0]])
                    build.send_webhook(webhook)
                    break
                e_ += results[source[0]]
            if e_ != []:
                src= source
                build = builder.Builder(src[1], src[0], avatars[src[0]], embeds=e_)
                build.send_webhook(webhook)
        if filtered != []:
            build = builder.Builder(content, src[0], avatars[src[0]], embeds=filtered)
            build.send_webhook(webhook)
        if len(embeds) > 10:
            for chunk in helpers.chunks(embeds):
                #print('r')
                build = builder.Builder(embeds=chunk)
                build.send_webhook(webhook)
        elif embeds != []:
            build = builder.Builder(embeds=embeds)
            build.send_webhook(webhook)

#import time

#s = time.time()
main()
#e = time.time()
#print(e-s)