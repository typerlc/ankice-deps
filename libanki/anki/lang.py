#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Internationalisation
=====================
"""
__docformat__ = 'restructuredtext'

import os, sys
import gettext

currentLang = "en_US"
currentTranslation = None

def _(str):
    return currentTranslation.ugettext(str)

def ngettext(single, plural, n):
    return currentTranslation.ungettext(single, plural, n)

def setLang(lang):
    base = os.path.dirname(os.path.abspath(__file__))
    localeDir = os.path.join(base, "locale")
    if not os.path.exists(localeDir):
        localeDir = os.path.join(
            os.path.dirname(sys.argv[0]), "locale")
    trans = gettext.translation('libanki', localeDir,
                                languages=[lang],
                                fallback=True)
    global currentLang, currentTranslation
    currentLang = lang
    currentTranslation = trans

def getLang():
    return currentLang

if not currentTranslation:
    setLang("en_US")
