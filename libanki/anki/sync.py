#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Synchronisation
==============================

Support for keeping two decks synchronized. Both local syncing and syncing
over HTTP are supported.

Server implements the following calls:

getDecks(): return a list of deck names & modtimes
summary(lastSync): a list of all objects changed after lastSync
applyPayload(payload): apply any sent changes and return any changed remote
                       objects
createDeck(name): create a deck on the server

"""
__docformat__ = 'restructuredtext'

import zlib, re, urllib, urllib2, socket, simplejson, time
from datetime import date
import anki, anki.deck, anki.cards
from anki.errors import *
from anki.models import Model, FieldModel, CardModel
from anki.facts import Fact, Field
from anki.cards import Card
from anki.stats import Stats, globalStats
from anki.history import CardHistoryEntry

if simplejson.__version__ < "1.7.3":
    raise "SimpleJSON must be 1.7.3 or later."

# Protocol 3 code
##########################################################################

class SyncTools(object):

    def __init__(self, deck=None):
        self.deck = deck
        self.diffs = {}

    def setServer(self, server):
        self.server = server

    def modified(self):
        return self.deck.modified

    def _lastSync(self):
        return self.deck.lastSync

    def unstuff(self, data):
        "Uncompress and convert to unicode."
        return simplejson.loads(zlib.decompress(data))

    def stuff(self, data):
        "Convert into UTF-8 and compress."
        return zlib.compress(simplejson.dumps(data))

    def dictFromObj(self, obj):
        "Return a dict representing OBJ without any hidden db fields."
        return dict([(k,v) for (k,v) in obj.__dict__.items()
                     if not k.startswith("_")])

    def applyDict(self, obj, dict):
        "Apply each element in DICT to OBJ in a way the ORM notices."
        for (k,v) in dict.items():
            setattr(obj, k, v)

    def realTuples(self, result):
        "Convert an SQLAlchemy response into a list of real tuples."
        return [tuple(x) for x in result]

    # Summaries
    ##########################################################################

    def summary(self, lastSync):
        "Generate a full summary of modtimes for two-way syncing."
        # ensure we're flushed first
        self.deck.s.flush()
        return {
            # cards
            "cards": self.realTuples(self.deck.s.all(
            "select id, modified from cards where modified > :mod",
            mod=lastSync)),
            "delcards": self.realTuples(self.deck.s.all(
              "select cardId, deletedTime from cardsDeleted "
              "where deletedTime > :mod", mod=lastSync)),
            # facts
            "facts": self.realTuples(self.deck.s.all(
            "select id, modified from facts where modified > :mod",
            mod=lastSync)),
            "delfacts": self.realTuples(self.deck.s.all(
              "select factId, deletedTime from factsDeleted "
              "where deletedTime > :mod", mod=lastSync)),
            # models
            "models": self.realTuples(self.deck.s.all(
            "select id, modified from models where modified > :mod",
            mod=lastSync)),
            "delmodels": self.realTuples(self.deck.s.all(
              "select modelId, deletedTime from modelsDeleted "
              "where deletedTime > :mod", mod=lastSync)),
            }

    # Diffing
    ##########################################################################

    def diffSummary(self, localSummary, remoteSummary, key):
        # list of ids on both ends
        lexists = localSummary[key]
        ldeleted = localSummary["del"+key]
        rexists = remoteSummary[key]
        rdeleted = remoteSummary["del"+key]
        ldeletedIds = dict(ldeleted)
        rdeletedIds = dict(rdeleted)
        # to store the results
        locallyEdited = []
        locallyDeleted = []
        remotelyEdited = []
        remotelyDeleted = []
        # build a hash of all ids, with value (localMod, remoteMod).
        # deleted/nonexisting cards are marked with a modtime of None.
        ids = {}
        for (id, mod) in rexists:
            ids[id] = [None, mod]
        for (id, mod) in rdeleted:
            ids[id] = [None, None]
        for (id, mod) in lexists:
            if id in ids:
                ids[id][0] = mod
            else:
                ids[id] = [mod, None]
        for (id, mod) in ldeleted:
            if id in ids:
                ids[id][0] = None
            else:
                ids[id] = [None, None]
        # loop through the hash, determining differences
        for (id, (localMod, remoteMod)) in ids.items():
            if localMod and remoteMod:
                # changed/existing on both sides
                if localMod < remoteMod:
                    remotelyEdited.append(id)
                elif localMod > remoteMod:
                    locallyEdited.append(id)
            elif localMod and not remoteMod:
                # if it's missing on server or newer here, sync
                if (id not in rdeletedIds or
                    rdeletedIds[id] < localMod):
                    locallyEdited.append(id)
                else:
                    remotelyDeleted.append(id)
            elif remoteMod and not localMod:
                # if it's missing locally or newer there, sync
                if (id not in ldeletedIds or
                    ldeletedIds[id] < remoteMod):
                    remotelyEdited.append(id)
                else:
                    locallyDeleted.append(id)
            else:
                if id in ldeletedIds and id not in rdeletedIds:
                   locallyDeleted.append(id)
                elif id in rdeletedIds and id not in ldeletedIds:
                   remotelyDeleted.append(id)
        return (locallyEdited, locallyDeleted,
                remotelyEdited, remotelyDeleted)

    # Control
    ##########################################################################

    def sync(self):
        "Sync two decks locally."
        self.localTime = self.modified()
        self.remoteTime = self.server.modified()
        l = self._lastSync(); r = self.server._lastSync()
        if l != r:
            self.lastSync = 0
        else:
            self.lastSync = l
        lsum = self.summary(self.lastSync)
        rsum = self.server.summary(self.lastSync)
        payload = self.genPayload(lsum, rsum)
        res = self.server.applyPayload(payload)
        self.applyPayloadReply(res)

    def genPayload(self, lsum, rsum):
        payload = {}
        # first, handle models, facts and cards
        for key in ("models", "facts", "cards"):
            diff = self.diffSummary(lsum, rsum, key)
            payload["added-" + key] = self.getObjsFromKey(diff[0], key)
            payload["deleted-" + key] = diff[1]
            payload["missing-" + key] = diff[2]
            self.deleteObjsFromKey(diff[3], key)
        # handle the remainder
        if self.localTime > self.remoteTime:
            payload['deck'] = self.bundleDeck()
            payload['stats'] = self.bundleStats()
            payload['history'] = self.bundleHistory()
            self.deck.lastSync = self.deck.modified
        return payload

    def applyPayload(self, payload):
        reply = {}
        # model, facts and cards
        for key in ("models", "facts", "cards"):
            # send back any requested
            reply['added-' + key] = self.getObjsFromKey(
                payload['missing-' + key], key)
            self.updateObjsFromKey(payload['added-' + key], key)
            self.deleteObjsFromKey(payload['deleted-' + key], key)
        # send back deck-related stuff if it wasn't sent to us
        if not 'deck' in payload:
            reply['deck'] = self.bundleDeck()
            reply['stats'] = self.bundleStats()
            reply['history'] = self.bundleHistory()
            self.deck.lastSync = self.deck.modified
        else:
            self.updateDeck(payload['deck'])
            self.updateStats(payload['stats'])
            self.updateHistory(payload['history'])
        self.postSyncRefresh()
        return reply

    def applyPayloadReply(self, reply):
        # model, facts and cards
        for key in ("models", "facts", "cards"):
            self.updateObjsFromKey(reply['added-' + key], key)
        # deck
        if 'deck' in reply:
            self.updateDeck(reply['deck'])
            self.updateStats(reply['stats'])
            self.updateHistory(reply['history'])
        self.postSyncRefresh()

    def postSyncRefresh(self):
        "Flush changes to DB, and reload object associations."
        self.deck.s.flush()
        self.deck.s.refresh(self.deck)
        self.deck.currentModel

    def getObjsFromKey(self, ids, key):
        return getattr(self, "get" + key.capitalize())(ids)

    def deleteObjsFromKey(self, ids, key):
        return getattr(self, "delete" + key.capitalize())(ids)

    def updateObjsFromKey(self, ids, key):
        return getattr(self, "update" + key.capitalize())(ids)

    # Models
    ##########################################################################

    def getModels(self, ids):
        return [self.bundleModel(id) for id in ids]

    def bundleModel(self, id):
        "Return a model representation suitable for transport."
        # force load of lazy attributes
        mod = self.deck.s.query(Model).get(id)
        mod.fieldModels; mod.cardModels
        m = self.dictFromObj(mod)
        m['fieldModels'] = [self.bundleFieldModel(fm) for fm in m['fieldModels']]
        m['cardModels'] = [self.bundleCardModel(fm) for fm in m['cardModels']]
        return m

    def bundleFieldModel(self, fm):
        d = self.dictFromObj(fm)
        if 'model' in d: del d['model']
        return d

    def bundleCardModel(self, cm):
        d = self.dictFromObj(cm)
        if 'model' in d: del d['model']
        return d

    def updateModels(self, models):
        for model in models:
            local = self.getModel(model['id'])
            # avoid overwriting any existing card/field models
            fms = model['fieldModels']; del model['fieldModels']
            cms = model['cardModels']; del model['cardModels']
            self.applyDict(local, model)
            self.mergeFieldModels(local, fms)
            self.mergeCardModels(local, cms)

    def getModel(self, id, create=True):
        "Return a local model with same ID, or create."
        for l in self.deck.models:
            if l.id == id:
                return l
        if not create:
            return
        m = Model()
        self.deck.models.append(m)
        return m

    def mergeFieldModels(self, model, fms):
        ids = []
        for fm in fms:
            local = self.getFieldModel(model, fm)
            self.applyDict(local, fm)
            ids.append(fm['id'])
        for fm in model.fieldModels:
            if fm.id not in ids:
                self.deck.deleteFieldModel(model, fm)

    def getFieldModel(self, model, remote):
        for fm in model.fieldModels:
            if fm.id == remote['id']:
                return fm
        fm = FieldModel()
        model.addFieldModel(fm)
        return fm

    def mergeCardModels(self, model, cms):
        ids = []
        for cm in cms:
            local = self.getCardModel(model, cm)
            self.applyDict(local, cm)
            ids.append(cm['id'])
        for cm in model.cardModels:
            if cm.id not in ids:
                self.deck.deleteCardModel(model, cm)

    def getCardModel(self, model, remote):
        for cm in model.cardModels:
            if cm.id == remote['id']:
                return cm
        cm = CardModel()
        model.addCardModel(cm)
        return cm

    def deleteModels(self, ids):
        for id in ids:
            model = self.getModel(id, create=False)
            if model:
                self.deck.deleteModel(model)

    # Facts
    ##########################################################################
    # in sql for efficiency

    def getFacts(self, ids):
        factIds = ",".join([str(i) for i in ids])
        return {
            'facts': self.realTuples(self.deck.s.all("""
select id, modelId, created, modified, tags, spaceUntil, lastCardId from facts
where id in (%s)""" % factIds)),
            'fields': self.realTuples(self.deck.s.all("""
select id, factId, fieldModelId, ordinal, value from fields
where factId in (%s)""" % factIds))
            }

    def updateFacts(self, factsdict):
        facts = factsdict['facts']
        fields = factsdict['fields']
        if not facts:
            return
        # update facts first
        dlist = [{
            'id': f[0],
            'modelId': f[1],
            'created': f[2],
            'modified': f[3],
            'tags': f[4],
            'spaceUntil': f[5],
            'lastCardId': f[6]
            } for f in facts]
        self.deck.s.execute("""
insert or replace into facts
(id, modelId, created, modified, tags, spaceUntil, lastCardId)
values
(:id, :modelId, :created, :modified, :tags, :spaceUntil, :lastCardId)""", dlist)
        # now fields
        dlist = [{
            'id': f[0],
            'factId': f[1],
            'fieldModelId': f[2],
            'ordinal': f[3],
            'value': f[4]
            } for f in fields]
        self.deck.s.execute("""
insert or replace into fields
(id, factId, fieldModelId, ordinal, value)
values
(:id, :factId, :fieldModelId, :ordinal, :value)""", dlist)

    def deleteFacts(self, ids):
        self.deck.deleteFacts(ids)

    # Cards
    ##########################################################################
    # in sql for efficiency

    def getCards(self, ids):
        return self.realTuples(self.deck.s.all("""
select id, factId, cardModelId, created, modified, tags, ordinal,
priority, interval, lastInterval, due, lastDue, factor,
firstAnswered, reps, successive, averageTime, reviewTime, youngEase0,
youngEase1, youngEase2, youngEase3, youngEase4, matureEase0,
matureEase1, matureEase2, matureEase3, matureEase4, yesCount, noCount,
question, answer, lastFactor from cards
where id in (%s)""" % ",".join([str(i) for i in ids])))

    def updateCards(self, cards):
        if not cards:
            return
        dlist = [{'id': c[0],
                  'factId': c[1],
                  'cardModelId': c[2],
                  'created': c[3],
                  'modified': c[4],
                  'tags': c[5],
                  'ordinal': c[6],
                  'priority': c[7],
                  'interval': c[8],
                  'lastInterval': c[9],
                  'due': c[10],
                  'lastDue': c[11],
                  'factor': c[12],
                  'firstAnswered': c[13],
                  'reps': c[14],
                  'successive': c[15],
                  'averageTime': c[16],
                  'reviewTime': c[17],
                  'youngEase0': c[18],
                  'youngEase1': c[19],
                  'youngEase2': c[20],
                  'youngEase3': c[21],
                  'youngEase4': c[22],
                  'matureEase0': c[23],
                  'matureEase1': c[24],
                  'matureEase2': c[25],
                  'matureEase3': c[26],
                  'matureEase4': c[27],
                  'yesCount': c[28],
                  'noCount': c[29],
                  'question': c[30],
                  'answer': c[31],
                  'lastFactor': c[32],
                  } for c in cards]
        self.deck.s.execute("""
insert or replace into cards
(id, factId, cardModelId, created, modified, tags, ordinal,
priority, interval, lastInterval, due, lastDue, factor,
firstAnswered, reps, successive, averageTime, reviewTime, youngEase0,
youngEase1, youngEase2, youngEase3, youngEase4, matureEase0,
matureEase1, matureEase2, matureEase3, matureEase4, yesCount, noCount,
question, answer, lastFactor)
values
(:id, :factId, :cardModelId, :created, :modified, :tags, :ordinal,
:priority, :interval, :lastInterval, :due, :lastDue, :factor,
:firstAnswered, :reps, :successive, :averageTime, :reviewTime, :youngEase0,
:youngEase1, :youngEase2, :youngEase3, :youngEase4, :matureEase0,
:matureEase1, :matureEase2, :matureEase3, :matureEase4, :yesCount,
:noCount, :question, :answer, :lastFactor)""", dlist)

    def deleteCards(self, ids):
        self.deck.deleteCards(ids)

    # Deck/stats/history
    ##########################################################################

    def bundleDeck(self):
        d = self.dictFromObj(self.deck)
        if 'acqQueue' in d:
            # revision queue
            del d['acqQueue']
            del d['revQueue']
            del d['failedQueue']
            del d['futureQueue']
            del d['factSpacing']
        del d['Session']
        del d['engine']
        del d['s']
        del d['path']
        del d['syncName']
        # these may be deleted before bundling
        if 'models' in d: del d['models']
        if 'currentModel' in d: del d['currentModel']
        return d

    def updateDeck(self, deck):
        self.applyDict(self.deck, deck)
        self.deck.lastSync = self.deck.modified

    def bundleStats(self):
        def bundleStat(stat):
            s = self.dictFromObj(stat)
            s['day'] = s['day'].toordinal()
            del s['id']
            return s
        lastDay = date.fromtimestamp(self.deck.lastSync)
        stats = {
            'global': bundleStat(globalStats(self.deck.s)),
            'daily': [bundleStat(s) for s in self.deck.s.query(Stats).\
                      filter(Stats.type == 1).\
                      filter(Stats.day >= lastDay).all()]
            }
        return stats

    def updateStats(self, stats):
        gs = globalStats(self.deck.s)
        stats['global']['day'] = date.fromordinal(stats['global']['day'])
        self.applyDict(gs, stats['global'])
        for record in stats['daily']:
            record['day'] = date.fromordinal(record['day'])
            stat = self.deck.s.query(Stats).filter_by(type=1).filter_by(
                day=record['day']).first()
            if not stat:
                stat = Stats(1)
                self.applyDict(stat, record)
                self.deck.s.save(stat)

    def bundleHistory(self):
        def bundleHist(hist):
            h = self.dictFromObj(hist)
            del h['id']
            return h
        hst = self.deck.s.query(CardHistoryEntry).filter(
            CardHistoryEntry.time > self.deck.lastSync)
        return [bundleHist(h) for h in hst]

    def updateHistory(self, history):
        for h in history:
            ent = CardHistoryEntry()
            self.applyDict(ent, h)
            self.deck.s.save(ent)

# Local syncing
##########################################################################

class SyncServer(SyncTools):
    pass

class SyncClient(SyncTools):
    pass

# HTTP proxy: act as a server and direct requests to the real server
##########################################################################

class HttpSyncServerProxy(SyncClient):

    def __init__(self, user, passwd):
        self.decks = None
        self.deckName = None
        self.username = user
        self.password = passwd
        self.syncURL="http://anki.ichi2.net/sync/"
        #self.syncURL="http://localhost:5000/sync/"
        self.protocolVersion = 2

    def connect(self, clientVersion=""):
        "Check auth, protocol & grab deck list."
        if not self.decks:
            d = self.runCmd("getDecks",
                            libanki=anki.version,
                            client=clientVersion)
            if d['status'] != "OK":
                raise SyncError(type="authFailed", status=d['status'])
            self.decks = d['decks']

    def hasDeck(self, deckName):
        self.connect()
        return deckName in self.decks.keys()

    def availableDecks(self):
        self.connect()
        return self.decks.keys()

    def createDeck(self, deckName):
        ret = self.runCmd("createDeck", name=deckName)
        if not ret or ret['status'] != "OK":
            raise SyncError(type="createFailed")
        self.decks[deckName] = [0, 0]

    def summary(self, lastSync):
        return self.runCmd("summary",
                           lastSync=self.stuff(lastSync))

    def modified(self):
        self.connect()
        return self.decks[self.deckName][0]

    def _lastSync(self):
        self.connect()
        return self.decks[self.deckName][1]

    def applyPayload(self, payload):
        return self.runCmd("applyPayload",
                           payload=self.stuff(payload))

    def runCmd(self, action, **args):
        data = {"d": self.deckName,
                "p": self.password,
                "u": self.username}
        data.update(args)
        data = urllib.urlencode(data)
        try:
            f = urllib2.urlopen(self.syncURL + action, data)
        except (urllib2.URLError, socket.error, socket.timeout):
            raise SyncError(type="noResponse")
        ret = f.read()
        if not ret:
            raise SyncError(type="noResponse")
        return self.unstuff(ret)

# HTTP server: respond to proxy requests and return data
##########################################################################

class HttpSyncServer(SyncServer):
    def __init__(self):
        SyncServer.__init__(self)
        self.protocolVersion = 2
        self.decks = {}
        self.deck = None

    def summary(self, lastSync):
        return self.stuff(SyncServer.summary(
            self, self.unstuff(lastSync)))

    def applyPayload(self, payload):
        return self.stuff(SyncServer.applyPayload(self,
            self.unstuff(payload)))

    def getDecks(self, libanki, client):
        return self.stuff({
            "status": "OK",
            "decks": self.decks,
            })

    def createDeck(self, name):
        "Create a deck on the server. Not implemented."
        return self.stuff("OK")
