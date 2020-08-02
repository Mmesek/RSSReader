import re

def filtr(embeds, regex):
    pattern = re.compile(regex)
    e_ = []
    for embed in embeds:
        #d = pattern.search(embed['description'])
        if pattern.search(embed['title']) != None:
            e_ += [embed]
    return e_

def chunks(array):
    for i in range(0, len(array), 10):
        yield array[i:i+10]

def cumulative(embed):
    total = 0
    t = []
    for field in embed.values():
        if type(field) is not int:
            t += field
    for v in t:
        total += len(v)
    return total

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


def getIfromRGB(rgb):
    red = int(rgb[0].strip())
    green = int(rgb[1].strip())
    blue = int(rgb[2].strip())
    RGBint = (red<<16) + (green<<8) + blue
    return RGBint
from PIL import ImageFile
import urllib
def get_main_color(img):
    file = urllib.request.urlopen(urllib.request.Request(img, headers={'User-Agent': 'Mozilla'}))#/JustCheckingImgSize'}))
    
    p = ImageFile.Parser()

    while 1:
        s = file.read(1024)
        if not s:
            break
        p.feed(s)

    im = p.close()
    r, g, b = im.getpixel((0, 0))
    return getIfromRGB((r, g, b))