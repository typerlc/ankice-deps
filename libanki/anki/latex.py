#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright: Damien Elmes <anki@ichi2.net>
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

"""\
Latex support
==============================
"""
__docformat__ = 'restructuredtext'

import re, tempfile, os, sys

latexPreamble = ("\\documentclass[12pt]{article}\n"
                 "\\pagestyle{empty}\n"
                 "\\begin{document}")
latexPostamble = "\\end{document}"
latexDviPngCmd = "dvipng -D 200 -T tight"

regexps = {
    "standard": re.compile(r"\[latex\](.+?)\[/latex\]", re.DOTALL | re.IGNORECASE),
    "expression": re.compile(r"\[\$\](.+?)\[/\$\]", re.DOTALL | re.IGNORECASE),
    "math": re.compile(r"\[\$\$\](.+?)\[/\$\$\]", re.DOTALL | re.IGNORECASE),
    }

tmpdir = tempfile.mkdtemp(prefix="anki-latex")

# add standard tex install location to osx
if sys.platform == "darwin":
    os.environ['PATH'] += ":/usr/texbin"

def renderLatex(deck, text):
    "Convert TEXT with embedded latex tags to image links."
    for match in regexps['standard'].finditer(text):
        text = text.replace(match.group(), imgLink(deck, match.group(1)))
    for match in regexps['expression'].finditer(text):
        text = text.replace(match.group(), imgLink(
            deck, "$" + match.group(1) + "$"))
    for match in regexps['math'].finditer(text):
        text = text.replace(match.group(), imgLink(
            deck,
            "\\begin{displaymath}" + match.group(1) + "\\end{displaymath}"))
    return text

def imgLink(deck, latex):
    "Parse LATEX and return a HTML image representing the output."
    from htmlentitydefs import entitydefs
    for match in re.compile("&([a-z]+);", re.IGNORECASE).finditer(latex):
        if match.group(1) in entitydefs:
            latex = latex.replace(match.group(), entitydefs[match.group(1)])
    latex = re.sub("<br( /)?>", "\n", latex)
    name = os.path.join(tmpdir, "%d.png" % hash(latex))
    log = os.path.join(tmpdir, "latex_log.txt")
    texpath = os.path.join(tmpdir, "tmp.tex")
    texfile = file(texpath, "w")
    texfile.write(latexPreamble + "\n")
    texfile.write(latex + "\n")
    texfile.write(latexPostamble + "\n")
    texfile.close()
    if not os.path.exists(name):
        oldcwd = os.getcwd()
        try:
            os.chdir(tmpdir)
            os.system("latex -interaction=nonstopmode %s >> %s 2>&1" % (texpath, log))
            os.system(latexDviPngCmd + " tmp.dvi -o %s >> %s" % (name, log))
        finally:
            os.chdir(oldcwd)
    return '<img src="%s">' % name
