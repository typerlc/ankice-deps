# coding: utf-8

import nose, os
from tests.shared import assertException

from anki.errors import *
from anki import DeckStorage
from anki.db import *
from anki.models import FieldModel
from anki.stdmodels import JapaneseModel, BasicModel

newPath = None
newModified = None

## opening/closing

def test_new():
    deck = DeckStorage.Deck()
    assert deck.path
    assert deck.engine
    assert deck.modified
    # for attachOld()
    global newPath, newModified
    newPath = deck.path
    deck.save()
    newModified = deck.modified
    deck.close()

def test_attachNew():
    path = "/tmp/test_attachNew"
    try:
        os.unlink(path)
    except OSError:
        pass
    deck = DeckStorage.Deck(path)
    deck.close()
    del deck
    os.unlink(path)

def test_attachOld():
    deck = DeckStorage.Deck(newPath)
    assert deck.modified == newModified
    deck.close()

def test_attachReadOnly():
    # non-writeable dir
    assertException(DeckAccessError,
                    lambda: DeckStorage.Deck("/attachroot"))
    # reuse tmp file from before, test non-writeable file
    os.chmod(newPath, 0)
    assertException(DeckAccessError,
                    lambda: DeckStorage.Deck(newPath))
    os.chmod(newPath, 0666)
    os.unlink(newPath)

def test_saveAs():
    path = "/tmp/test_saveAs"
    try:
        os.unlink(path)
    except OSError:
        pass
    deck = DeckStorage.Deck()
    deck.addModel(BasicModel())
    # add a card
    f = deck.newFact()
    f['Front'] = u"foo"; f['Back'] = u"bar"
    deck.addFact(f)
    # save in new deck
    newDeck = deck.saveAs(path)
    assert newDeck.totalCardCount() == 1
    newDeck.close()
    deck.close()

def test_factAddDelete():
    deck = DeckStorage.Deck()
    deck.addModel(BasicModel())
    # set rollback point
    deck.s.commit()
    f = deck.newFact()
    # empty fields
    try:
        deck.addFact(f)
    except Exception, e:
        pass
    assert e.data['type'] == 'fieldEmpty'
    # add a fact
    f['Front'] = u"one"; f['Back'] = u"two"
    deck.addFact(f)
    assert len(f.cards) == 1
    deck.rollback()
    # try with two cards
    f = deck.newFact()
    f['Front'] = u"one"; f['Back'] = u"two"
    f.model.cardModels[1].active = True
    deck.addFact(f)
    assert len(f.cards) == 2
    # ensure correct order
    c0 = [c for c in f.cards if c.ordinal == 0][0]
    assert c0.question == u"one"
    # now let's make a duplicate
    f2 = deck.newFact()
    f2['Front'] = u"one"; f2['Back'] = u"three"
    try:
        deck.addFact(f2)
    except Exception, e:
        pass
    assert e.data['type'] == 'fieldNotUnique'
    # try delete the first card
    deck.deleteCard(f.cards[0].id)
    # and the second should clear the fact
    deck.deleteCard(f.cards[1].id)

def test_cardOrder():
    deck = DeckStorage.Deck()
    deck.addModel(JapaneseModel())
    f = deck.newFact()
    f['Expression'] = u'1'
    f['Meaning'] = u'2'
    deck.addFact(f)
    card = deck.getCard()
    # production should come first
    assert card.cardModel.name == u"Production"
    # if we rebuild the queue, it should be the same
    deck.rebuildQueue()
    card = deck.getCard()
    assert card.cardModel.name == u"Production"

def test_modelAddDelete():
    deck = DeckStorage.Deck()
    deck.addModel(JapaneseModel())
    f = deck.newFact()
    f['Expression'] = u'1'
    f['Meaning'] = u'2'
    deck.addFact(f)
    assert deck.totalCardCount() == 2
    deck.deleteModel(deck.currentModel)
    assert deck.totalCardCount() == 0
    deck.s.refresh(deck)
    assert deck.currentModel == None
