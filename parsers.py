import html2text, re, requests
from bs4 import BeautifulSoup as bs

def parseSteam(embed, desc, entry='', desc_=''):
    h2t = html2text.HTML2Text()
    h2tl = (
        h2t.handle(desc_.prettify())
        .replace("{LINK REMOVED}", "")
    )
    links = re.findall(r"( ?\n? ?\[((?s).*?) ?\n? ?\] ?\n? ?\(((?s).*?)\)\n?)", h2tl)
    for l in links:
        if l[1].replace('\n','').strip() == l[2].replace('\n','').strip():
            h2tl = h2tl.replace(l[0], '/n' + l[0].replace('\n', '').replace(' ', ''))
        if 'linkfilter' in l[2]:
            nlink = l[2].split('linkfilter/?url=')[1].replace(' ','').replace('\n','')
            h2tl = h2tl.replace(l[2], nlink)
        h2tl = h2tl.replace(l[2], l[2].replace(' ', '').replace('\n', ''))
        h2tl = h2tl.replace(l[1], l[1].replace('\n','').replace('[ ','[').replace(' ]',']'))
    try:
        #if desc.img["src"][-4:] != ".gif":
            #imag = desc.img["src"]
        imag = desc.find("img")["src"]
    except:
        imag = ''
    h2tl = h2tl.replace(f"![]({imag})", "")
    images = re.findall(r"\!\[\]\(\S*\)", h2tl)
    for image in images:
        h2tl = h2tl.replace(f"{image}", "")
    if '!' in h2tl[0]:
        h2tl = h2tl[1:]
    h2tl = h2tl.strip()
    links_all = re.findall(r"\((https://store.steam\S*)\)", h2tl)
    for link_ in links_all:
        link = link_.split('?',1)[0]
        if link[-1] != '/':
            link+='/'
        s = link.split("/")[-2].replace("_", " ")
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link_}]({link_})", "")
        store_id = re.search(r'/\d+/', link)
        if store_id is not None:
            store_id = f'\nOpen in Steam: steam://store{store_id[0]}'
        else:
            store_id = ''
        embed.addField("Steam Store", f"[{s}]({link}){store_id}", True)
    events = re.findall(r"\((\S*/partnerevents/view/\S*)\)", h2tl)
    for link in events:
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link}]({link})", "")
        embed.addField("Steam Event", f"[View Event]({link})", True)
    help_ = re.findall(r'\((https://help.steam\S*)\)', h2tl)
    for link in help_:
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link}]({link})", "")
        embed.addField("Steam Support", f"[{link.split('/')[-1]}]({link})", True)
    community = re.findall(r'(\[((?s).*?)\] ?\(((?s)steamcommunity.com\S*)\))', h2tl)
    for link in community:
        h2tl = h2tl.replace(f"[\n", "[").replace(f"[{link[0]}]({link[1]})", "")
        embed.addField("Steam Community", f"[{link[0]}]({link[1]})", True)
    if '\n__' in h2tl:
        h2tl = re.sub('\n__', '/n----/n', h2tl)
        h2tl = re.sub('___', '', h2tl)
    h2tl = h2tl.replace('\n\n','/n').replace('\n',' ').replace('/n','\n').replace(' ,',',').replace(' .','.').replace(' " ','"')
    return h2tl

def parsePurePC(embed, desc, entry='', desc_=''):
    netflix = re.search(r'(?i)netflix|(hbo go)', entry['title'])
    releases = re.search(r'(?i)Premiery gier', entry['title'])
    if netflix != None or releases != None:
        desc = ''
        bdata = requests.get(entry['link'], headers={'Accept':'text/html', 'User-Agent': 'Mozzila'})
        soup = bs(bdata.text, 'html.parser')
        if netflix != None:
            try:
                glist = soup.find('div', class_='main').findAll('li')
                #glist = soup.find('div',class_='main').findAll('h3',class_='cyt')
                tags = False
                for each in glist[1:]:
                    #desc+=f'\n- {each.text}'
                    if 'class' in each.attrs:
                        for one in each.attrs['class']:
                            if 'taxonomy_term' in one:
                                tags = True
                    if tags:
                        break
                    h2t = html2text.HTML2Text()
                    h2tl = h2t.handle(each.prettify())
                    if len(h2tl) + len(desc) <= 2024:
                        desc += f'\n- {h2tl}'.replace(' * ', ' ')  #{each.text}'
                    else:
                        break
            except Exception as ex:
                desc = bs(entry['description'],'html.parser').text.split('.',3)
                desc = desc[0]+f'. {desc[1]}. {desc[2]}.'
        elif releases != None:
            try:
                glist = soup.find('table',class_='specy').findAll('tr')
                dates = {}
                for each in glist[1:]:
                    row = each.findAll('td')
                    if row[0].text not in dates:
                        dates[row[0].text] = []
                    if len(row) == 3:
                        dates[row[0].text] += [f"{row[1].text} - {row[2].text}"]
                for date in dates:
                    desc+=f'\n**{date}**:'
                    for game in dates[date]:
                        desc+=f'\n- {game}'
            except Exception as ex:
                desc = bs(entry['description'],'html.parser').text.split('.',3)
                desc = desc[0]+f'. {desc[1]}. {desc[2]}.'
    else:
        desc = bs(entry['description'],'html.parser').text.split('.',3)
        desc = desc[0] + f'. {desc[1]}. {desc[2]}.'
    return desc

def parseCDAction(embed, desc, entry='', desc_=''):
    desc = bs(entry['description'], 'html.parser').text
    cena = re.findall("tym razem (\d*,\d*) zł", desc)
    try:
        desc = desc.split('pełne wersje:', 1)[1].split('Cena cz', 1)[0].replace('– ', '\n- ').replace('Do numeru', '\nDo numeru') + "\nCena: " + cena[0]
    except:
        pass
    return desc

def parseGGDeals(embed, desc, entry, desc_):
    if not any(t in entry['link'] for t in ['bundle', 'choice', 'game-pass', 'origin-access']):
        return desc
    bdata = requests.get(entry['link'])
    soup = bs(bdata.text, 'html.parser')
    if not any(t in entry['link'] for t in ['choice', 'game-pass', 'origin-access']):
        try:
            glist = soup.find('div', class_='wrap_items').find('div', class_='list').findAll('a', class_='ellipsis title')  #.text
        except:
            return desc
    else:
        glist = soup.find('div', class_='text-content-wrapper news-content shadow-box box-assets-shadow box-assets-responsive').find('ul').findAll('li')
    desc = ''
    for each in glist:
        desc += f'\n- {each.text}'
    return desc


def parseLowcy(embed, desc, entry='', desc_=''):
    desc = bs(entry['description'], 'html.parser')
    potrwa = re.findall(r"Oferta potrwa (\d*) dni", desc.text)
    link = ''
    dni = re.findall(r"(\d*) dni darmowej gry", desc.text)
    rabat = re.findall(r"i do ((\d*) (.*))\b zakupić grę z (\d*)% rabatem \(za (.*) zł\)", desc.text)
    desc = ''
    desc += ''
    return desc.text
#    (r"(?i)(za darmo)? ?(?=PC|Steam|uPlay|Origin|Bethesda|Discord|Epic Games Store|GOG|Humble Store).*? ?(?=za darmo)?")
#    (r"(?i)za darmo (na|za|w|po) (.*?) (PC|Steam|Uplay|Origin|Bethesda|Discord|Epic Games Store|GOG|Humble Store|Alienware)")
#    (r"(?i)(darmowy weekend|dni darmowej gry|darmowy tydzień|graj za darmo|bet(y|a))")

def polskigamdev(embed, desc, entry='', desc_=''):
    if '#ZostanWDomuGrajWPolskieGry'.lower() not in entry['title'].lower():
        return desc
    table = {
        '(': '0',
        '@': '1',
        '!': '2',
        '#': '3',
        '%': '4',
        '$': '5',
        '^': '6',
        '&': '7',
        ':': '8',
        ')': '9',        
    }
    data = requests.get(entry['link'])
    soup = bs(data.text, 'html.parser')
    ls = soup.blockquote
    if ls is not None:
        ls = ls.text
        for char in table:
            ls = ls.replace(char, table[char])
        return ls
    return desc

def itad(embed, desc, entry, desc_):
    if True:#'[bundle]' in entry['title'] and ('humble' in entry['title'].lower() or 'fanatical' in entry['title'].lower()):
        h2t = html2text.HTML2Text()
        #desc = h2t.handle(re.sub(' : ?(.*?) |','',desc_.prettify()))
        desc = h2t.handle(desc_.prettify())
        a = re.findall(r'\[ ?(.*?)\n? ?\] ?\((.*?)\)', desc)
        f= ''
        if a is not None:
            for i in a:
                if 'see details' in i[0]:
                    f += '\n' +'['+i[0].title()+']('+i[1]+')'
                else:
                    f += '\n- ' + i[0]
        end = re.findall(r'(?:expires on (.*?) )|(unknown expiry)', desc)
        for one in end:
            f+='\nExpires on **'+''.join(one)+'**'
        #desc = re.sub(': (.*?) |', '',desc)
        #v = h2t.handle(f.prettify())
        return f
    return ''

from textwrap import wrap
def parseKapitanHack(embed, desc, entry, desc_):
    if 'zestawienie tygodniowe' in entry['title'].lower():
        desc = ''
        bdata = requests.get(entry['link'], headers={'Accept':'text/html', 'User-Agent': 'Mozzila'})
        soup = bs(bdata.text, 'html.parser')
        try:
            glist = soup.find('div', class_='entry-content')
            headers = glist.findAll('h5')
            bodies = glist.findAll('p')
            total_characters = 0
            field_count = 0
            for x, each in enumerate(headers[:-1]):
                body = bodies[x]
                h2t = html2text.HTML2Text()
                h2tl = h2t.handle(body.prettify())
                if (total_characters+len(each.text)+len(body.text)) < 6000 and field_count < 25:
                    for x, chunk in enumerate(wrap(body.text, 1024, break_on_hyphens=True, break_long_words=True)):
                        if x == 0:
                            embed.addField(each.text, chunk, False)
                        elif total_characters < 6000:
                            embed.addField('\u200b', chunk, False)
                        total_characters += len(each.text) + len(chunk)
                        field_count += 1
        except Exception as ex:
            desc = bs(entry['description'],'html.parser').text.split('.',3)
            desc = desc[0] + f'. {desc[1]}. {desc[2]}.'
    return desc

def parseppe(embed, desc, entry, desc_):
    if 'hbo go' in entry['title'].lower():
        desc = ''
        bdata = requests.get(entry['link'], headers={'Accept': 'text/html', 'User-Agent': 'Mozzila'})
        soup = bs(bdata.text, 'html.parser')
        daily = False
        try:
            glist = soup.find('div', itemprop='articleBody')
            headers = glist.findAll('h2')
            for header in headers:
                if 'dzień po dniu' in header.text:
                    list_start = header.next_siblings
            days = {}
            last = None
            for i in list_start:
#                print(i)
                if i.name == 'p':
                    days[i.text] = []
                    last = i.text
                else:
                    if last is not None:
                        if hasattr(i, 'text'):
                            #print(i)
                            days[last].append(i.text)
            releases = ''
            releases_days = []
            for day in days:
                if days[day] != []:
                    _day = '\n'.join(days[day])
                    day = day.replace('\xa0',' ')
                    if len(releases[:1020]) + len(day) + len(_day) < 1016:
                        releases += '\n' + f"**{day}**" + _day
                        releases_days.append(day)
                    else:
                        if len(releases_days) > 1:
                            related_days = releases_days[0].split(' ')[0] + '-' + releases_days[-1]
                        else:
                            related_days = releases_days[0]
                        releases_days = []
                        #print(related_days, releases)
                        embed.addField(related_days, releases)
                        releases = ''
                        if len(releases[:1020]) + len(day) + len(_day) < 1016:
                            releases += '\n' + f"**{day}**" + _day
                            releases_days.append(day)
            if releases != '':
                if len(releases_days) > 1:
                    related_days = releases_days[0].split(' ')[0] + '-' + releases_days[-1]
                else:
                    related_days = releases_days[0]
                #print(related_days, releases)
                embed.addField(related_days, releases)
        except Exception as ex:
            desc = bs(entry['description'],'html.parser').text.split('.',3)
            desc = desc[0] + f'. {desc[1]}. {desc[2]}.'
    return desc