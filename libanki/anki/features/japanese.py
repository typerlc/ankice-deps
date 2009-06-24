#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

import sys, os
from anki.features import Feature
from anki.utils import findTag, parseTags, stripHTML

class KakasiController(object):
    def __init__(self):
        # add our pre-packaged kakasi to the path
        if sys.platform == "win32":
            dir = os.path.dirname(sys.argv[0])
            os.environ['PATH'] += ";" + dir + "\\kakasi\\bin"
            shareDir = dir + "\\kakasi\\share\\kakasi\\"
            os.environ['ITAIJIDICT'] = shareDir + "\\itaijidict"
            os.environ['KANWADICT'] = shareDir + "\\kanwadict"
        elif sys.platform.startswith("darwin"):
            dir = os.path.dirname(os.path.abspath(__file__))
            dir = os.path.abspath(dir + "/../../../../..")
            import platform
            # don't add kakasi to the path on powerpc, it's buggy
            # and loop until this works, since processor() is buggy
            while 1:
                try:
                    proc = platform.processor()
                except IOError:
                    proc = None
                if proc:
                    break
            if proc != "powerpc":
                os.environ['PATH'] += ":" + dir + "/kakasi"
            os.environ['ITAIJIDICT'] = dir + "/kakasi/itaijidict"
            os.environ['KANWADICT'] = dir + "/kakasi/kanwadict"
        self._open = False

    # we don't launch kakasi until it's actually required
    def lazyopen(self):
        if not self._open:
            if not self.available():
                from errno import ENOENT
                raise OSError(ENOENT, 'Kakasi not available')
            # don't convert kana to hiragana
            (self.kin, self.kout) = os.popen2("kakasi -isjis -osjis -u -JH -p")
            self._open = True

    def close(self):
        if self._open:
            self.kin.close()
            self.kout.close()

    def toFurigana(self, kanji):
        self.lazyopen()
        kanji = self.formatForKakasi(kanji)
        try:
            self.kin.write(kanji.encode("sjis", "ignore")+'\n')
            self.kin.flush()
            return unicode(self.kout.readline().rstrip('\n'), "sjis")
        except IOError:
            return u""

    def formatForKakasi(self, text):
        "Strip characters kakasi can't handle."
        # kakasi is line based
        text = text.replace("\n", " ")
        text = text.replace(u'\uff5e', "~")
        text = text.replace("<br>", "---newline---")
        text = text.replace("<br />", "---newline---")
        text = stripHTML(text)
        text = text.replace("---newline---", "<br>")
        return text

    def available(self):
        if sys.platform in ("win32",):
            executable = 'kakasi.exe'
        else:
            executable = 'kakasi'
        for d in os.environ['PATH'].split(os.pathsep):
            if os.path.exists(os.path.join(d, executable)):
                return True
        return False

class FuriganaGenerator(Feature):

    def __init__(self):
        self.tags = ["Japanese"]
        self.name = "Furigana generation based on kakasi."
        self.kakasi = KakasiController()
        if not self.kakasi.available():
            self.kakasi = None

    def onKeyPress(self, fact, field, value):
        if self.kakasi and findTag("Reading source",
                                   parseTags(field.fieldModel.features)):
            reading = self.kakasi.toFurigana(value)
            dst = None
            for field in fact.fields:
                if findTag("Reading destination", parseTags(
                    field.fieldModel.features)):
                    dst = field
                    break
            if dst:
                if self.kakasi.formatForKakasi(value) != reading:
                    fact[dst.name] = reading
                else:
                    fact[dst.name] = u""
