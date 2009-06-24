#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Cards
====================
"""
__docformat__ = 'restructuredtext'

import time, sys, math, random
from anki.db import *
from anki.models import CardModel, Model, FieldModel
from anki.facts import Fact, factsTable, Field
from anki.utils import parseTags, findTag, stripHTML, genID

# Cards
##########################################################################

cardsTable = Table(
    'cards', metadata,
    Column('id', Integer, primary_key=True),
    Column('factId', Integer, ForeignKey("facts.id"), nullable=False, index=True),
    Column('cardModelId', Integer, ForeignKey("cardModels.id"), nullable=False),
    Column('created', Float, nullable=False, default=time.time),
    Column('modified', Float, nullable=False, default=time.time),
    Column('tags', UnicodeText, nullable=False, default=u""),
    Column('ordinal', Integer, nullable=False),
    # cached - changed on fact update
    Column('question', UnicodeText, nullable=False, default=u""),
    Column('answer', UnicodeText, nullable=False, default=u""),
    # default to 'normal' priority
    Column('priority', Integer, nullable=False, default=2),
    Column('interval', Float, nullable=False, default=0),
    Column('lastInterval', Float, nullable=False, default=0),
    Column('due', Float, nullable=False, default=time.time),
    Column('lastDue', Float, nullable=False, default=0),
    Column('factor', Float, nullable=False, default=2.5),
    Column('lastFactor', Float, nullable=False, default=2.5),
    Column('firstAnswered', Float, nullable=False, default=0),
    # stats
    Column('reps', Integer, nullable=False, default=0),
    Column('successive', Integer, nullable=False, default=0),
    Column('averageTime', Float, nullable=False, default=0),
    Column('reviewTime', Float, nullable=False, default=0),
    Column('youngEase0', Integer, nullable=False, default=0),
    Column('youngEase1', Integer, nullable=False, default=0),
    Column('youngEase2', Integer, nullable=False, default=0),
    Column('youngEase3', Integer, nullable=False, default=0),
    Column('youngEase4', Integer, nullable=False, default=0),
    Column('matureEase0', Integer, nullable=False, default=0),
    Column('matureEase1', Integer, nullable=False, default=0),
    Column('matureEase2', Integer, nullable=False, default=0),
    Column('matureEase3', Integer, nullable=False, default=0),
    Column('matureEase4', Integer, nullable=False, default=0),
    # this duplicates the above data, because there's no way to map imported
    # data to the above
    Column('yesCount', Integer, nullable=False, default=0),
    Column('noCount', Integer, nullable=False, default=0))

class Card(object):
    "A card."

    def __init__(self, fact=None, cardModel=None):
        self.tags = u""
        self.id = genID()
        if fact:
            self.fact = fact
        if cardModel:
            self.cardModel = cardModel
            self.ordinal = cardModel.ordinal
            self.question = cardModel.renderQA(self, self.fact, "question")
            self.answer = cardModel.renderQA(self, self.fact, "answer")

    htmlQuestion = property(lambda self: self.cardModel.renderQA(
        self, self.fact, "question", format="html"))
    htmlAnswer = property(lambda self: self.cardModel.renderQA(
        self, self.fact, "answer", format="html"))

    def setModified(self):
        self.modified = time.time()

    def startTimer(self):
        self.lastShown = time.time()
        self._thinkingTime = None

    def thinkingTime(self):
        "End the timer if it's running, and return the last delay."
        if self._thinkingTime:
            return self._thinkingTime
        self._thinkingTime = time.time() - self.lastShown
        return self._thinkingTime

    def css(self):
        return self.cardModel.css() + self.fact.css()

    def genFuzz(self):
        "Generate a random offset to spread intervals."
        self.fuzz = random.uniform(0.95, 1.05)

    def updateStats(self, ease, state):
        self.reps += 1
        if ease > 1:
            self.successive += 1
        else:
            self.successive = 0
        delay = self.thinkingTime()
        # ignore any times over 60 seconds
        if delay < 60:
            self.reviewTime += delay
            if self.averageTime:
                self.averageTime = (self.averageTime + delay) / 2.0
            else:
                self.averageTime = delay
        # we don't track first answer for cards
        if state == "new":
            state = "young"
        # update ease and yes/no count
        attr = state + "Ease%d" % ease
        setattr(self, attr, getattr(self, attr) + 1)
        if ease < 2:
            self.noCount += 1
        else:
            self.yesCount += 1
        if not self.firstAnswered:
            self.firstAnswered = time.time()
        self.setModified()

    def hasTag(self, tag):
        alltags = parseTags(self.tags + "," +
                            self.fact.tags + "," +
                            self.cardModel.name + "," +
                            self.fact.model.tags)
        return findTag(tag, alltags)

mapper(Card, cardsTable, properties={
    'cardModel': relation(CardModel),
    'fact': relation(Fact, backref="cards", primaryjoin=
                     cardsTable.c.factId == factsTable.c.id),
    })

mapper(Fact, factsTable, properties={
    'model': relation(Model),
    'fields': relation(Field, backref="fact", order_by=Field.c.ordinal),
    'lastCard': relation(Card, post_update=True, primaryjoin=
                         cardsTable.c.id == factsTable.c.lastCardId),
    })

# Card deletions
##########################################################################

cardsDeletedTable = Table(
    'cardsDeleted', metadata,
    Column('cardId', Integer, ForeignKey("cards.id"),
           nullable=False, index=True),
    Column('deletedTime', Float, nullable=False))
