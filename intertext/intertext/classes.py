# -*- coding: utf-8 -*-

# classes.py
###############################################################################
# Written by Arno Simons

# Released under GNU General Public License, version 3.0

# Copyright (c) 2017 Arno Simons

# This file is part of Intertext.

# Intertext is free software: you can redistribute it and/or modify it under 
# the terms of the GNU General Public License as published by the Free 
# Software Foundation, either version 3 of the License, or (at your option) any
 # later version.

# Intertext is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with 
# Intertext. If not, see <http://www.gnu.org/licenses/>.
###############################################################################

import os
import types
import distance
import weakref
import collections
import networkx as nx
from pyzotero import zotero

from intertext.constants import * 

### Actor Class
###############################################################################
class Actor(object):
    """
    Create an ``Actor``::

        >>> a = intertext.Actor(name='Foucault, Michel')

    """
    _universe = set()
    _originals = set()

    def __init__(self, **attr):
        if u'name' in attr.iterkeys():
            self.name = attr.pop(u'name')
        elif u'lastname' in attr.iterkeys():
            if u'firstname' in attr.iterkeys():
                self.name = u', '.join(
                    [attr.pop(u'lastname'), attr.pop(u'firstname')])
            else:
                self.name = attr.pop(u'lastname')
        else:
            raise ValueError(u"Provide name or lastname".format(attr))
        self.attr = attr # or {}
        label = self.name
        while label in [a().label for a in Actor._universe]:
            label += u'*'
        self._label = label
        self._is_copy = any(self.is_like(a()) for a in Actor._universe)
        Actor._originals.add(weakref.ref(self._original))
        Actor._universe.add(weakref.ref(self))

    def __repr__(self):
        return self.label

    def call_label(self):
        return self._label

    @property
    def label(self):
        return self._label

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name):
        if not isinstance(name, basestring):
            raise ValueError
        if not RE_NAME.match(name):
            raise ValueError
        self._name = name
        splitname = [n for n in name.split(u', ')]
        self.lastname = splitname[0]
        if len(splitname) == 2:
            self.firstname = splitname[1]
        else:
            self.firstname = u''

    @property
    def lastname(self):
        return self._lastname

    @lastname.setter
    def lastname(self, lastname):
        if not isinstance(lastname, basestring):
            raise ValueError
        if not RE_LASTNAME.match(lastname):
            raise ValueError
        self._lastname = lastname

    @property
    def firstname(self):
        return self._firstname

    @firstname.setter
    def firstname(self, firstname):
        if not isinstance(firstname, basestring):
            raise ValueError
        if not firstname:
            self._firstname = firstname
            return
        if not RE_FIRSTNAME.match(firstname):
            raise ValueError
        self._firstname = firstname

    @property
    def _original(self):
        for a in Actor._originals:
            if self.is_like(a()):
                return a()
        return self
    
    @property
    def is_copy(self):
        return self._is_copy

    def is_like(self, other):
        if not isinstance(other, Actor):
            raise ValueError
        return (
            self.name == other.name
            and self.attr.viewitems() <= other.attr.viewitems()
            )

    def is_in(self, others):
        return any(self.is_like(i) for i in others)

    def compares_to(self, other):
        if not isinstance(other, Actor):
            raise ValueError
        # e.g. for abbreviated firstname or missing second firstname



### Text Class
###############################################################################
class Text(object):
    """
    Create a ``Text``::

        >>> t = intertext.Text(title=u"L'Archéologie du savoir", date=u'1969')

    """
    _universe = set()
    _originals = set()

    def __init__(self, **attr):
        if not all(k in attr.iterkeys() for k in [u'title', u'date']):
            raise ValueError
        self.title = attr.pop(u'title')
        self.date = attr.pop(u'date')
        self.authors = attr.pop(u'authors', [])
        self.editors = attr.pop(u'editors', [])
        self.cites = attr.pop(u'cites', [])
        # self.cited_by = attr.pop(u'cited_by', [])

        # build properties/setters for all these:
        self.type = attr.pop(u'type', u'text')
        self.publisher = attr.pop(u'publisher', [])
        self.pages = attr.pop(u'pages', u'')
        self.doi = attr.pop(u'doi', u'')
        self.references = attr.pop(u'references', [])
        # check typical attributes...

        self.attr = attr # or {}
        label = self.short
        while label in [d().label for d in Text._universe]:
            label += u'*'
        self._label = label
        self._is_copy = any(self.is_like(t()) for t in Text._universe)
        Text._originals.add(weakref.ref(self._original))
        Text._universe.add(weakref.ref(self))

    def __repr__(self):
        return self.label

    def call_label(self):
        return self._label

    @property
    def label(self):
        return self._label

    @property
    def short(self):
        year = self.year
        title = u'_'.join(self.title[:15].split())
        short = u'_'.join([year, title]) 
        return short

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        if not isinstance(title, basestring):
            raise ValueError
        self._title = title

    @property
    def date(self):
        return self._date

    @date.setter
    def date(self, date):
        if not isinstance(date, basestring):
            raise ValueError
        # test if date satisfies regex
        if not RE_VALID_DATE.match(date):
            raise ValueError(
                u'Check documentation for correct formatting of date')
        self._date = date

    @property
    def year(self):
        return re.findall(YEAR, self.date)[0]

    @property
    def authors(self):
        return self._authors

    @property
    def firstauthor(self):
        return self._authors[0] if self._authors else None

    @authors.setter
    def authors(self, authors):
        self._authors = []
        self.add_authors(authors)

    def add_authors(self, authors):
        if isinstance(authors, list):
            for i in authors:
                if isinstance(i, Actor):
                    if not i._original in self._authors:
                        self._authors.append(i._original)
                elif isinstance(i, dict):
                    candidate = Actor(**i)
                    if not candidate._original in self._authors:
                        self._authors.append(candidate._original)
                else:
                    raise ValueError(u'Authors in list must be Actor or dict')
        elif isinstance(authors, Actor):
            if not authors._original in self._authors:
                self._authors.append(authors._original)
        elif isinstance(authors, dict):
            candidate = Actor(**i)
            if not candidate._original in self._authors:
                self._authors.append(candidate._original)
        else:
            raise ValueError(u'Authors must be list, Actor, or dict')

    @property
    def editors(self):
        return self._editors

    @editors.setter
    def editors(self, editors):
        self._editors = []
        self.add_editors(editors)

    def add_editors(self, editors):
        if isinstance(editors, list):
            for i in editors:
                if isinstance(i, Actor): 
                    if not i._original in self._editors:
                        self._editors.append(i._original)
                elif isinstance(i, dict):
                    candidate = Actor(**i)
                    if not candidate._original in self._editors:
                        self._editors.append(candidate._original)
                else:
                    raise ValueError(u'Editors in list must be Actor or dict')
        elif isinstance(editors, Actor):
            if not editors._original in self._editors:
                self._editors.append(editors._original)
        elif isinstance(editors, dict):
            candidate = Actor(**i)
            if not candidate._original in self._editors:
                self._editors.append(candidate._original)
        else:
            raise ValueError(u'Editors must be list, Actor, or dict')

    @property
    def cites(self):
        return sorted(list(self._cites), key=Text.call_label, reverse=True)

    @cites.setter
    def cites(self, others):
        self._cites = set()
        self.add_citations_to(others)

    def add_citations_to(self, others):
        if isinstance(others, list):
            for i in others:
                if isinstance(i, Text): 
                    self._cites.add(i._original)
                elif isinstance(i, dict):
                    candidate = Text(**i)
                    self._cites.add(candidate._original)
                else:
                    raise ValueError(u'Citations in list must be Text or dict')
        elif isinstance(others, Text):
            self._cites.add(others._original)
        elif isinstance(others, dict):
            candidate = Text(**i)
            self._cites.add(candidate._original)
        else:
            raise ValueError(u'Citations must be list, Text, or dict')

    def cited_by(self, population):
        if isinstance(population, Intertext):
            population = population._texts
        if not (
            isinstance(population, (list, set, tuple)) 
            and all(isinstance(i, Text) for i in population)
            ):
                raise ValueError(u'Poulation must be iterable and can only contain Text elements')
        return sorted([t for t in population if self in t.cites], key=Text.call_label, reverse=True)

    @property
    def _original(self):
        for t in Text._originals: # narrow selection?
            if self.is_like(t()):
                return t()
        return self

    @property
    def is_copy(self):
        return self._is_copy

    def is_like(self, other):
        if not isinstance(other, Text):
            raise ValueError
        return (
            self.title == other.title
            and self.year == other.year
            and self.attr.viewitems() <= other.attr.viewitems() # https://stackoverflow.com/questions/9323749/python-check-if-one-dictionary-is-a-subset-of-another-larger-dictionary/35416899
            )

    def is_in(self, others):
        return any(self.is_like(i) for i in others)

    def compares_to(self, other, nlev=0.1, date_span=(4,4)):
        if not isinstance(other, Text):
            raise ValueError
        return 1 if (
            self.is_like(other)
            ) else 2 if (
            self.year == other.year
            and distance.nlevenshtein(
                self.title, other.title, method=2) <= nlev
            ) else 3 if (
            self.title == other.title
            and int(self.year) + date_span[1]
            >= int(other.year)
            >= int(self.year) - date_span[0]
            ) else 4 if (
            distance.nlevenshtein(
                self.title, other.title, method=2) <= nlev
            and int(self.year) + date_span[1]
            >= int(other.year)
            >= int(self.year) - date_span[0]
            ) else 99

    def best_matches_in(self, population, match_hierarchy=MATCH_HIERARCHY):
        if not isinstance(population, list) and not all(isinstance(i, Text) for i in population):
            raise ValueError
        matches = collections.defaultdict(list)
        for k,v in ((self.compares_to(t), t) for t in population):
            matches[k].append(v)
        # print matches
        for i in match_hierarchy:
            if matches[i]:
                return (matches[i], i)



### Intertext Class
###############################################################################
class Intertext(object):

    def __init__(self, name, texts=None):
        if not isinstance(name, basestring):
            raise ValueError
        self.texts = texts

    @property
    def texts(self):
        return sorted(list(self._texts), key=Text.call_label)

    @texts.setter
    def texts(self, texts):
        self._texts = set()
        if texts:
            self.add_texts(texts)

    def add_texts(self, texts):
        if isinstance(texts, list):
            for i in texts:
                if isinstance(i, Text):
                    self._texts.add(i._original)
                elif isinstance(i, dict):
                    self._texts.add(Text(**i)._original)
                else:
                    raise ValueError(u'Texts in list must be Text or dict')
        elif isinstance(texts, Text):
            self._texts.add(texts._original)
        elif isinstance(texts, dict):
            self._texts.add(Text(**i)._original)
        else:
            raise ValueError(u'Texts must be list, Text, or dict')

    @property
    def authors(self):
        return sorted(list(set(a for t in self._texts for a in t.authors)), key=Actor.call_label)

    @property
    def editors(self):
        return sorted(list(set(a for t in self._texts for a in t.editors)), key=Actor.call_label)

    @property
    def co_authors(self):
        edgelist = ((d,a) for d in self._texts for a in d.authors)
        return co_occurrences(edgelist)

    @property
    def co_editors(self):
        edgelist = ((d,a) for d in self._texts for a in d.editors)
        return co_occurrences(edgelist)

    @property
    def cited_texts(self):
        return sorted(set([c for t in self._texts for c in t.cites]), key=Text.call_label)

    @property
    def citations(self):
        return [(d,c) for d in self._texts for c in d.cites]

    @property
    def co_citations(self):
        edgelist = ((d,c) for d in self._texts for c in d.cites)
        return co_occurrences(edgelist)

    @property
    def bibliographic_coupling(self):
        edgelist = ((d,c) for d in self._texts for c in d.cites)
        return co_occurrences(edgelist, focus=u'source')

    def load_Zotero(self, Z):
        for i in Z.texts:
            self.add_texts(
                Text(
                    title=i[u'title'],
                    date=i[u'date'],
                    authors=[Actor(
                        lastname=c[u'lastName'],
                        firstname=c[u'firstName']
                        ) for c in i[u'creators'] if c[u'creatorType'] == u'author'],
                    editors=[Actor(
                        lastname=c[u'lastName'],
                        firstname=c[u'firstName']
                        ) for c in i[u'creators'] if c[u'creatorType'] == u'editor'],
                    )
                )



### Zotero class
###############################################################################
class Zotero(object):
    
    def __init__(self, api_key, library_id, library_type, collection_id=None):
        print u'Establishing Zotero handler...'
        if collection_id == None:
            raise ValueError
        self.web = zotero.Zotero(library_id, library_type, api_key)
        self.library_id = library_id
        self.library_type = library_type
        self.api_key = api_key
        self.collection_id = collection_id
        self.refresh()

    def refresh(self):
        self._data = [i[u'data'] for i in self.web.everything(
                    self.web.collection_items(self.collection_id))]

    @property
    def data(self):
        return self._data

    @property
    def texts(self):
        return [i for i in self._data if not any(
            i[u'itemType'] == t for t in [u'attachment', u'note'])]

    @property
    def attachments(self):
        return [i for i in self._data 
            if i[u'itemType'] == u'attachment']

    @property
    def cit_notes(self):
        return [i for i in self._data 
            if i[u'itemType'] == u'note'
            and u'parentItem' in i.iterkeys()
            and u'RDA citations' in [t.values()[0] for t in i[u'tags']]]
    
    @property
    def cit_files(self):
        return [i for i in self._data 
            if i[u'itemType'] == u'attachment'
            and any(
                i[u'contentType'] == t for t in [u'text/html', u'text/plain'])
            and u'parentItem' in i.iterkeys()
            and u'RDA citations' in [t.values()[0] for t in i[u'tags']]]
        
    @property
    def rawtexts(self):
        return [i for i in self._data
            if i['itemType'] == u'attachment' 
            and all(k in i.iterkeys() for k in [u'parentItem', u'path'])
            and u'RDA rawtext' in [t.values()[0] for t in i[u'tags']]]
    @property
    def cleantexts(self):
        return [i for i in self._data
            if i[u'itemType'] == u'attachment' 
            and all(k in i.iterkeys() for k in [u'parentItem', u'path'])
            and u'RDA cleantext' in [t.values()[0] for t in i[u'tags']]]

    def item_by_key(self, key):
        result = [i for i in self._data if i.get(u'key') == key]
        print len(result)
        if result:
            if len(result) > 1:
                raise ValueError(u'more than one item with key "{}"'.format(key))
            return result[0]
        return None