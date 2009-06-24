|logo| PocketPyGui readme
=========================

:Author: Alexandre Delattre
:Date: 26/01/08
:Version: ppygui-0.5

Background
----------

PocketPyGui is a native GUI toolkit for PythonCE, 
it is an 'almost from scratch' rewrite of the
VensterCE toolkit with a brand new API.

Indeed, even knowing a bit the Win32 API from a C++ 
point of view, 
I found tiresome to always do the same low-level stuff for
simple GUIs and to always have to look in MSDN for some Win32 API 
reference. 

Besides, even if I did write a tutorial for it, I admit 
it is quite difficult to get in VensterCE for a python dev without Win32 API experience. The lack of API docs for VensterCE was
not a problem for ones used to dig in MSDN, but was a pain for all others.

Anyway, porting Venster to WinCE was a good experience as
I learned a lot from it, and it was my first open-source contribution.

So I decided to take the good stuff of VensterCE (native, ligthweight and pure python library) and
create a toolkit by python developers for python developers.

The major features of PocketPyGui are:

    - Rich common-controls library (almost all VensterCE widgets supported and more).
      with pythonic APIs (i.e. zero knowledge of Win32 API).
    - Transparent event-handling: you associate gui events to 
      your callbacks, and ppygui will call them at the right time.
    - Flexible layout system: ppygui revamps the VensterCE layout system
      and you can now let ppygui compute the size of your controls based on
      their contents and fonts.
    - Automatic unicode coercion: you can use raw and unicode strings.

Requirements
------------

* PythonCE >= 2.4.
* **HIGHLY RECOMMENDED**: 
  a WinCE task manager for really closing windows when pressing the X button is really advised for better experience
  with ppygui. I suggest you `tMan <http://pda.jasnapaka.com/tman/>`_, which is freeware, but any other
  task mananger should be ok.

Archive contents
----------------

Ppygui will come in three packages:

* ppygui.zip package 
    The core library, docs and a simple demo.

    - install.py: the graphical installer (start with this).
    - doc/: contains the quick-start tutorial and its scripts, the API reference and auto-generated docs.
    - ppygui/: the toolkit source.
    - demo.py: a simple demo application for an overview of ppygui controls.
    
* ppygui-samples.zip package 
    Useful applications to learn ppygui from sources.
    
    - demo/canvas/: the WIP canvas control.
    - demo/app/outliner/: a tree-view based task outliner.
    - demo/app/restEditor/: a simple reStructuredText editor for html/latex generation (requires docutils).
    - demo/app/mpc/: a MPD (Music Player Daemon) client.
    - demo/app/jabberce/: a simple Jabber client (requires tlslite and xmpppy).
    
* ppygui-3rdparty-tools.zip
    Libraries and tools tweaked to run with PythonCE or gathered here for convenience.
    Be sure to read the respective licenses of these great tools.
    
    - tlslite/: implementation of SSL/TLS and other security protocols (required for JabberCE).
    - xmpppy/: a Jabber protocol library (required for JabberCE).
    - docutils/: API and command line tools for reStructuredText processing (required for restEditor).
    
    
Installation
------------

* Extract the archive on your pda (warning some sd-mmc card readers tends to uppercase some files ...).

* Run install.py and let the graphical installer guide you !

Documentation
-------------

PocketPyGui documentation is splitted in:

* a tutorial_.
* the `API reference`_.

.. _tutorial : doc/ppygui-doc.html
.. _`API reference` : doc/ppygui-api.html 

Contact
-------

You can post your questions/suggestions on
the ppygui sourceforge forum page 
(http://sf.net/projects/ppygui).


Copyright
---------

PocketPyGui is released under the BSD License.
Samples and 3rd party apps shipped with PocketPyGui
are subject to their own license.

Credits
-------

Special Thanks to Mirko "D@ten" Vogt.

.. |logo| image:: python.bmp
