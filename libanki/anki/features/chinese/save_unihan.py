# read unihan.txt and save it as a db

import psyco; psyco.full()

from sqlalchemy import (Table, Integer, Float, Unicode, Column, MetaData,
                        ForeignKey, Boolean, String, Date, UniqueConstraint,
                        UnicodeText)
from sqlalchemy import (create_engine)
from sqlalchemy.orm import mapper, sessionmaker, relation, backref, \
     object_session as _object_session
from sqlalchemy.sql import select, text, and_
from sqlalchemy.exceptions import DBAPIError

metadata = MetaData()

unihanTable = Table(
    'unihan', metadata,
    Column("id", Integer, primary_key=True),
    Column("mandarin", UnicodeText),
    Column("cantonese", UnicodeText),
    Column("grade", Integer),
    )

engine = create_engine("sqlite:///unihan.db",
                       echo=False, strategy='threadlocal')
session = sessionmaker(bind=engine,
                       autoflush=False,
                       transactional=True)
metadata.create_all(engine)

s = session()

kanji = {}
import codecs
for line in codecs.open("Unihan.txt", encoding="utf-8"):
    try:
        (u, f, v) = line.strip().split("\t")
    except ValueError:
        continue
    if not u.startswith("U+"):
        continue
    n = int(u.replace("U+",""), 16)
    if not n in kanji:
        kanji[n] = {}
    if f == "kMandarin":
        kanji[n]['mandarin'] = v
    elif f == "kCantonese":
        kanji[n]['cantonese'] = v
    elif f == "kGradeLevel":
        kanji[n]['grade'] = int(v)

dict = [{'id': k,
         'mandarin': v.get('mandarin'),
         'cantonese': v.get('cantonese'),
         'grade': v.get('grade') } for (k,v) in kanji.items()
        if v.get('mandarin') or v.get('cantonese') or v.get('grade')]
s.execute(unihanTable.insert(), dict)


s.commit()
