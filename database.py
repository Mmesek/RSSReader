from sqlalchemy import Column, String, Integer, BigInteger, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
Base = declarative_base()

class Sources(Base):
    __tablename__ = 'RSS'
    Source = Column(String, primary_key=True)
    Last = Column(Integer)
    URL = Column(String)
    Color = Column(Integer)
    Language = Column(String)
    AvatarURL = Column(String)
    #Type = Column(String)
    #Interval = Column(Integer)
    #LastFetched = Column(Integer)

class Webhooks(Base):
    __tablename__ = 'Webhooks'
    GuildID = Column(BigInteger, primary_key=True)
    Webhook = Column(String)
    Source = Column(String, primary_key=True)
    Content = Column(String)
    Regex = Column(String)
    AddedBy = Column(BigInteger)

class Spotify(Base):
    __tablename__ = 'Spotify'
    SpotifyID = Column(String, primary_key=True)
    Artist = Column(String)
    AddedBy = Column(BigInteger)

class Database:
    def __init__(self):
        c = ConfigToDict()["Database"]
        self.engine = create_engine(f"{c['db']}://{c['user']}:{c['password']}@{c['location']}:{c['port']}/{c['name']}")
        #self.engine = create_engine("postgresql://postgres:postgres@r4:5432/mframework")
        self.Session = sessionmaker(bind=self.engine)

    def update(self, source: str, last: int) -> None:
        session = self.Session()
        src = session.query(Sources).filter(Sources.Source == source).first()
        src.Last = last
        session.commit()
    def getSources(self) -> list:  #(tuple(str)):
        session = self.Session()
        sources = session.query(Sources).all()
        sources = [(row.Source, row.Last, row.URL, row.Color, row.Language, row.AvatarURL) for row in sources]
        return sources
        
    def getWebhooks(self) -> list:  #(str):
        session = self.Session()
        webhooks = session.query(Webhooks.Webhook, Webhooks.Source, Webhooks.Content, Webhooks.Regex).all()
        webhooks_ = {}
        for webhook in webhooks:
            if webhook not in webhooks_:
                webhooks_[webhook.Webhook] = []
            webhooks_[webhook.Webhook] += [(row.Source, row.Content, row.Regex) for row in webhooks if row.Webhook == webhook.Webhook]
        
        return webhooks_

    def getSpotifyWebhooks(self) -> list:
        session = self.Session()
        webhooks = session.query(Webhooks.Webhook).filter(Webhooks.Source == 'Spotify').all()
        return webhooks

    def getObservedArtists(self) -> list:
        session = self.Session()
        artists = session.query(Spotify.SpotifyID, Spotify.Artist).all()
        return artists

    def getTodayWebhooks(self) -> list:
        session = self.Session()
        return session.query(Webhooks.Webhook).filter(Webhooks.Source == 'Today').all()
        
import configparser
from os.path import dirname
def ConfigToDict():
    dictonary = {}
    config = configparser.ConfigParser()
    config.read(dirname(__file__)+'/config.ini')
    sections = config.sections()
    for section in sections:
        dictonary[section] = {}
        for option in config.options(section):
            try:
                value = config.get(section, option)
                if value.isdigit():
                    value = config.getint(section, option)
                elif value.lower() in ['true', 'false', 'yes', 'no', 'on', 'off']:
                    value = config.getboolean(section, option)
                dictonary[section][option] = value
            except Exception as ex:
                print("Exception while reading from config file: ", ex)
                dictonary[section][option] = None
    return dictonary