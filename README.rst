.. contents::

Introduction
============

``plone.requirements.txt`` is the collection of plone releases each requirements.txt file is compiled from version.cfg file.


How To Use
==========

More than one ways you can use each requirements.txt file.


Include in local requirements.txt
---------------------------------

So easy to include as `recursive requirements as described here <https://pip.readthedocs.io/en/1.1/requirements.html#recursive-requirements>`_

Example::

    -r https://raw.githubusercontent.com/collective/plone.requirements.txt/master/dist/<your plone release version>/requirements.txt


Directly mention to pip executable
----------------------------------


``$ <path>/pip install -r https://raw.githubusercontent.com/collective/plone.requirements.txt/master/dist/<your plone release version>/requirements.txt``

FAQ
===

Distribution Not Found
----------------------

Sometimes pip might not found old/zope/plone specific packages, in that case you will need to bellows links in your requirements.txt file

Example::

    --find-links http://dist.plone.org/packages'
    --find-links http://dist.plone.org/thirdparty
    --trusted-host dist.plone.org'
    --find-links http://download.zope.org/distribution/
    --trusted-host download.zope.org
    --find-links http://effbot.org/downloads
    --trusted-host effbot.org
    --find-links http://pypi.python.org/simple/
    --trusted-host pypi.python.org


Contributors
============

- Md Nazrul Islam (Author), email2nazrul@gmail.com



License
=======

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License version 2
as published by the Free Software Foundation.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston,
MA 02111-1307 USA.