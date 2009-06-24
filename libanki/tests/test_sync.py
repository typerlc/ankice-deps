# coding: utf-8

import nose, os
from tests.shared import assertException

from anki.errors import *
from anki import DeckStorage
from anki.db import *
from anki.stdmodels import BasicModel, JapaneseModel
from anki.sync import SyncClient, SyncServer, HttpSyncServer, HttpSyncServerProxy
from anki.stats import dailyStats, globalStats
from anki.facts import Fact
from anki.cards import Card
from anki.models import FieldModel

import psyco; psyco.full()

# Local tests
##########################################################################

deck1=None
deck2=None
client=None
server=None

def setup_local():
    global deck1, deck2, client, server
    deck1 = DeckStorage.Deck()
    deck1.addModel(BasicModel())
    deck1.currentModel.cardModels[1].active = True
    deck1.newCardOrder = 1
    f = deck1.newFact()
    f['Front'] = u"foo"; f['Back'] = u"bar"
    deck1.addFact(f)
    deck2 = DeckStorage.Deck()
    deck2.addModel(BasicModel())
    deck2.currentModel.cardModels[1].active = True
    f = deck2.newFact()
    f['Front'] = u"baz"; f['Back'] = u"qux"
    deck2.addFact(f)
    # ensure a defined order in getCard()
    deck2.newCardOrder = 1
    client = SyncClient(deck1)
    server = SyncServer(deck2)
    client.setServer(server)

def teardown():
    pass

@nose.with_setup(setup_local, teardown)
def test_localsync_diffing():
    assert deck1.totalCardCount() == 2
    assert deck2.totalCardCount() == 2
    lsum = client.summary(deck1.lastSync)
    rsum = server.summary(deck1.lastSync)
    result = client.diffSummary(lsum, rsum, 'cards')
    assert len(result[0]) == 2
    assert len(result[1]) == 0
    assert len(result[2]) == 2
    assert len(result[3]) == 0
    result = client.diffSummary(lsum, rsum, 'facts')
    assert len(result[0]) == 1
    assert len(result[1]) == 0
    assert len(result[2]) == 1
    assert len(result[3]) == 0

@nose.with_setup(setup_local, teardown)
def test_localsync_deck():
    # deck two was modified last
    assert deck2.modified > deck1.modified
    d2mod = deck2.modified
    assert deck1.lastSync == 0 and deck2.lastSync == 0
    client.sync()
    assert deck1.modified == deck2.modified
    assert deck1.lastSync == deck1.modified
    assert deck1.lastSync == deck2.lastSync
    # ensure values are being synced
    deck1.lowPriority += u",foo"
    deck1.updateAllPriorities()
    deck1.setModified()
    client.sync()
    assert "foo" in deck2.lowPriority
    assert deck1.modified == deck2.modified
    assert deck1.lastSync == deck2.lastSync
    deck2.description = u"newname"
    deck2.setModified()
    client.sync()
    assert deck1.description == u"newname"
    # the most recent change should take precedence
    deck1.description = u"foo"
    deck1.setModified()
    deck2.description = u"bar"
    deck2.setModified()
    client.sync()
    assert deck1.description == "bar"
    # answer a card to ensure stats & history are copied
    c = deck1.getCard()
    deck1.answerCard(c, 4)
    client.sync()
    assert dailyStats(deck2.s).reps == 1
    assert globalStats(deck2.s).reps == 1
    assert deck2.s.scalar("select count(id) from reviewHistory") == 1

@nose.with_setup(setup_local, teardown)
def test_localsync_models():
    client.sync()
    # add a model
    deck1.addModel(JapaneseModel())
    assert len(deck1.models) == 3
    assert len(deck2.models) == 2
    client.sync()
    assert len(deck2.models) == 3
    assert deck1.currentModel.id == deck2.currentModel.id
    # delete the recently added model
    deck2.deleteModel(deck2.currentModel)
    assert len(deck2.models) == 2
    client.sync()
    assert len(deck1.models) == 2
    assert deck1.currentModel.id == deck2.currentModel.id
    # make a card model inactive
    assert deck1.currentModel.cardModels[1].active == True
    deck2.currentModel.cardModels[1].active = False
    deck2.currentModel.setModified()
    deck2.setModified()
    client.sync()
    assert deck1.currentModel.cardModels[1].active == False
    # remove a card model
    deck1.deleteCardModel(deck1.currentModel,
                          deck1.currentModel.cardModels[1])
    deck1.currentModel.setModified()
    deck1.setModified()
    assert len(deck1.currentModel.cardModels) == 1
    client.sync()
    assert len(deck2.currentModel.cardModels) == 1
    # add a field
    c = deck1.getCard()
    deck1.addFieldModel(c.fact.model, FieldModel(u"yo"))
    deck1.s.refresh(c.fact)
    assert len(c.fact.fields) == 3
    assert c.fact['yo'] == u""
    client.sync()
    c2 = deck2.s.query(Card).get(c.id)
    deck2.s.refresh(c2.fact)
    assert c2.fact['yo'] == u""
    # remove the field
    assert "yo" in c2.fact.keys()
    deck2.deleteFieldModel(c2.fact.model, c2.fact.model.fieldModels[2])
    deck2.s.refresh(c2.fact)
    assert "yo" not in c2.fact.keys()
    client.sync()
    deck1.s.refresh(c.fact)
    assert "yo" not in c.fact.keys()
    # rename a field
    assert u"Front" in c.fact.keys()
    deck1.renameFieldModel(deck1.currentModel,
                           deck1.currentModel.fieldModels[0],
                           u"Sideways")
    client.sync()
    assert deck2.currentModel.fieldModels[0].name == u"Sideways"

@nose.with_setup(setup_local, teardown)
def test_localsync_factsandcards():
    assert deck1.totalFactCount() == 1 and deck1.totalCardCount() == 2
    assert deck2.totalFactCount() == 1 and deck2.totalCardCount() == 2
    client.sync()
    assert deck1.totalFactCount() == 2 and deck1.totalCardCount() == 4
    assert deck2.totalFactCount() == 2 and deck2.totalCardCount() == 4
    # ensure the fact was copied across
    f1 = deck1.s.query(Fact).first()
    f2 = deck1.s.query(Fact).get(f1.id)
    f1['Front'] = u"myfront"
    f1.setModified()
    deck1.setModified()
    client.sync()
    f2 = deck1.s.query(Fact).get(f1.id)
    assert f2['Front'] == u"myfront"
    deck1.rebuildQueue()
    deck2.rebuildQueue()
    c1 = deck1.getCard()
    c2 = deck2.getCard()
    assert c1.id == c2.id

@nose.with_setup(setup_local, teardown)
def test_localsync_threeway():
    # deck1 (client) <-> deck2 (server) <-> deck3 (client)
    deck3 = DeckStorage.Deck()
    client2 = SyncClient(deck3)
    server2 = SyncServer(deck2)
    client2.setServer(server2)
    client.sync()
    client2.sync()
    # add a new question
    f = deck1.newFact()
    f['Front'] = u"a"; f['Back'] = u"b"
    cards = deck1.addFact(f)
    card = cards[0]
    client.sync()
    assert deck1.totalCardCount() == 6
    assert deck2.totalCardCount() == 6
    # check it propagates from server to deck3
    client2.sync()
    assert deck3.totalCardCount() == 6
    # delete a card on deck1
    deck1.deleteCard(card.id)
    client.sync()
    assert deck1.totalCardCount() == 5
    assert deck2.totalCardCount() == 5
    # make sure the delete is now propagated from the server to deck3
    client2.sync()
    assert deck3.totalCardCount() == 5

# @nose.with_setup(setup_local, teardown)
# def test_localsync_upgradeAndSync():
#     base = "/home/resolve/tango-test.anki"
#     d1n = "/home/resolve/tango-test1.anki"
#     d2n = "/home/resolve/tango-test2.anki"
#     import shutil
#     from anki.importing import anki03
#     for i in (d1n, d2n):
#         try:
#             os.unlink(i)
#         except OSError:
#             pass
#         shutil.copy2(base, i)
#     # upgrade each deck
#     d1 = DeckStorage.Deck()
#     d2 = DeckStorage.Deck()
#     i = anki03.Anki03Importer(d1, d1n)
#     i.doImport()
#     i = anki03.Anki03Importer(d2, d2n)
#     i.doImport()

#     client = SyncClient(d1)
#     server = SyncServer(d2)
#     client.setServer(server)

#     lsum = client.summary(d1.lastSync)
#     rsum = server.summary(d1.lastSync)
#     for key in ("models", "facts", "cards"):
#         diff = client.diffSummary(lsum, rsum, key)
#         print diff

#     d1.setModified()
#     d1.currentModel.setModified()
#     client.sync()

#     lsum = client.summary(d1.lastSync)
#     rsum = server.summary(d1.lastSync)
#     for key in ("models", "facts", "cards"):
#         diff = client.diffSummary(lsum, rsum, key)
#         print diff

#     client.sync()

# Remote tests
##########################################################################

# a replacement runCmd which just calls our server directly
def runCmd(action, *args, **kargs):
    #print action, kargs
    return server.unstuff(apply(getattr(server, action), tuple(args) +
                                tuple(kargs.values())))

def setup_remote():
    setup_local()
    global client, server
    proxy = HttpSyncServerProxy("test", "foo")
    client = SyncClient(deck1)
    client.setServer(proxy)
    proxy.deckName = "test"
    proxy.runCmd = runCmd
    server = HttpSyncServer()
    server.deck = deck2
    server.decks = {"test": (deck2.modified, 0)}

@nose.with_setup(setup_remote, teardown)
def test_remotesync_fromserver():
    # deck two was modified last
    assert deck2.modified > deck1.modified
    client.sync()
    assert deck2.modified == deck1.modified

@nose.with_setup(setup_remote, teardown)
def test_remotesync_toserver():
    deck1.setModified()
    client.sync()
    assert deck2.modified == deck1.modified
