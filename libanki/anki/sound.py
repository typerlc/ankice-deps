#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Sound support
==============================
"""
__docformat__ = 'restructuredtext'

import re, sys

try:
    import pygame
    pygame.mixer.pre_init(44100,-16,2, 1024 * 3)
    pygame.mixer.init()
    soundsAvailable = True
except:
    soundsAvailable = False
    print "Warning, pygame not available. No sounds will play."

def play(path):
    "Play a sound. Expects a unicode pathname."
    if not soundsAvailable:
        return
    path = path.encode(sys.getfilesystemencoding())
    if pygame.mixer.music.get_busy():
        pygame.mixer.music.queue(path)
    else:
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
        except pygame.error:
            return

def playFromText(text):
    for match in re.findall("\[sound:(.*?)\]", text):
        play(match)

def stripSounds(text):
    return re.sub("\[sound:.*?\]", "", text)

def hasSound(text):
    return re.search("\[sound:.*?\]", text) is not None
