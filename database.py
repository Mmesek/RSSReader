#from __future__ import annotations
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

class Webhooks(Base):
    __tablename__ = 'Webhooks'
    GuildID = Column(BigInteger, primary_key=True)
    Webhook = Column(String)
    Source = Column(String, primary_key=True)
    Content = Column(String)
    Regex = Column(String)
    AddedBy = Column(BigInteger)

class Database:
    def __init__(self):
        self.engine = create_engine("postgresql://postgres:postgres@raspberry:5432/mbot")
        self.Session = sessionmaker(bind=self.engine)

    def update(self, source: str, last: int) -> None:
        session = self.Session()
        #sources = session.query(Sources.Source == source)
        #sources.update({"Last":last})
        src = session.query(Sources).filter(Sources.Source == source).first()
        src.Last = last
        #.update(Sources).where(Sources.Source==source).values(Last=last)
        session.commit()
    def getSources(self) -> list:  #(tuple(str)):
        session = self.Session()
        sources = session.query(Sources).all()
        sources = [(row.Source, row.Last, row.URL, row.Color, row.Language, row.AvatarURL) for row in sources]
        return sources
        return [(
                'Łowcy Gier', #Name
                0, #Last
                'https://lowcygier.pl/feed/', #Url
                0, #Color
                'pl', #Language
                None, #Avatar
                ),
                ('PurePC', 0, 'https://www.purepc.pl/rss_all.xml', 1, 'pl', None)]
    def getWebhooks(self) -> list:  #(str):
        session = self.Session()
        webhooks = session.query(Webhooks.Webhook, Webhooks.Source, Webhooks.Content, Webhooks.Regex).all()
        webhooks_ = {}
        for webhook in webhooks:
            if webhook not in webhooks_:
                webhooks_[webhook.Webhook] = []
            webhooks_[webhook.Webhook] += [(row.Source, row.Content, row.Regex) for row in webhooks if row.Webhook == webhook.Webhook]
        
        return webhooks_
        return [(
            'WEBHOOK', #Webhook Url
            [
                ('Łowcy Gier', '@darmoffe', 'darmo'),
                ('Łowcy Gier', None, None),  #Source, Content, Regex
                ('PurePC', None, 'Netflix'),
            ] #Included Sources
        )]