#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Importing Anki 0.9+ decks
==========================
"""
__docformat__ = 'restructuredtext'

from anki import DeckStorage
from anki.importing import Importer
from anki.sync import SyncClient, SyncServer

class Anki10Importer(Importer):

    needMapper = False

    def doImport(self):
        "Import."
        src = DeckStorage.Deck(self.file)
        client = SyncClient(self.deck)
        server = SyncServer(src)
        # if there is a conflict, sync local -> src
        client.localTime = self.deck.modified
        client.remoteTime = 0
        src.s.execute("update facts set modified = 1")
        src.s.execute("update models set modified = 1")
        src.s.execute("update cards set modified = 1")
        self.deck.s.flush()
        # set up a custom change list and sync
        lsum = client.summary(0)
        rsum = server.summary(0)
        payload = client.genPayload(lsum, rsum)
        # no need to add anything to src
        payload['added-models'] = []
        payload['added-cards'] = []
        payload['added-facts'] = {'facts': [], 'fields': []}
        payload['deleted-facts'] = []
        payload['deleted-cards'] = []
        payload['deleted-models'] = []
        res = server.applyPayload(payload)
        client.applyPayloadReply(res)
        # add tags
        fids = [f[0] for f in res['added-facts']['facts']]
        self.deck.addFactTags(fids, self.tagsToAdd)
        self.total = len(res['added-facts']['facts'])
        src.s.rollback()
        self.deck.flushMod()
