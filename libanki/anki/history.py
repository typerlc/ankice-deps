#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
History - keeping a record of all reviews
==========================================
"""
__docformat__ = 'restructuredtext'

import time
from anki.db import *

reviewHistoryTable = Table(
    'reviewHistory', metadata,
    Column('id', Integer, primary_key=True),
    Column('cardId', Integer, ForeignKey("cards.id")),
    Column('time', Float, nullable=False, default=time.time),
    Column('lastInterval', Float, nullable=False),
    Column('nextInterval', Float, nullable=False),
    Column('ease', Integer, nullable=False),
    Column('delay', Float, nullable=False),
    Column('lastFactor', Float, nullable=False),
    Column('nextFactor', Float, nullable=False),
    Column('reps', Float, nullable=False),
    Column('thinkingTime', Float, nullable=False),
    Column('yesCount', Float, nullable=False),
    Column('noCount', Float, nullable=False))

class CardHistoryEntry(object):
    "Create after rescheduling card."

    def __init__(self, card=None, ease=None, delay=None):
        if not card:
            return
        self.cardId = card.id
        self.lastInterval = card.lastInterval
        self.nextInterval = card.interval
        self.lastFactor = card.lastFactor
        self.nextFactor = card.factor
        self.reps = card.reps
        self.yesCount = card.yesCount
        self.noCount = card.noCount
        self.ease = ease
        self.delay = delay
        self.thinkingTime = card.thinkingTime()

mapper(CardHistoryEntry, reviewHistoryTable)
