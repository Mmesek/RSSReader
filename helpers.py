import re

def filtr(embeds, regex):
    pattern = re.compile(regex)
    e_ = []
    for embed in embeds:
        if pattern.search(embed['description']) != None or pattern.search(embed['title']) != None:
            e_ += [embed]
    return e_

def chunks(array):
    for i in range(0, len(array), 10):
        yield array[i:i+10]


import urllib
from PIL import ImageFile

def getsizes(uri):
    # get file size *and* image size (None if not known)
    try:
        file = urllib.request.urlopen(uri)
    except:
        try:
            file = urllib.request.urlopen(urllib.request.Request(uri, headers={'User-Agent': 'Mozilla'}))#/JustCheckingImgSize'}))
        except Exception as ex:
            #print('welp', ex)
            return (0, (0,0))
    size = file.headers.get("content-length")
    if size: 
        size = int(size)
    p = ImageFile.Parser()
    while True:
        data = file.read(1024)
        if not data:
            break
        p.feed(data)
        if p.image:
            return size, p.image.size
            break
    file.close()
    return(size, None)
