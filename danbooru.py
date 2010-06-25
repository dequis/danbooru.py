# -*- coding: utf-8 -*-
from __future__ import print_function # requires python 2.6
import os
import sys
import urllib
import urllib2
import sqlite3 # for the tags database
import functools
import lxml.etree

BASE_URL = 'http://danbooru.donmai.us/%s?%s'
HEADERS = {
    'Cookie': open("cookie.txt").read().strip(),
    'User-Agent': 'danbooru.py/0.2 (dx)'
}

TAG_TYPES = {
    0: 'general',
    1: 'artist',
    3: 'copyright',
    4: 'character',
}

# add reverse too
for (x, y) in TAG_TYPES.items():
    TAG_TYPES[y] = x


def request(method, params, parse=True):
    url = BASE_URL % (method, urllib.urlencode(params))
    print(url, file=sys.stderr)
    rc = urllib2.urlopen(urllib2.Request(url, None, HEADERS))
    if not parse:
        return rc
    return lxml.etree.XML(rc.read())

def api(method, **defaults):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(self, **kwds):
            params = defaults.copy()
            params.update(kwds)
            return f(self, request(method, params))
        return wrapper
    return decorator

def paged(f):
    '''Adds a keyword argument pages (-1 to return all)'''
    @functools.wraps(f)
    def wrapper(self, pages=1, start=0, *args, **kwds):
        page = start
        while pages != 0:
            thispage = f(self, *args, page=page, **kwds)
            for item in thispage:
                yield item

            if (int(self.pages_info['offset']) >=
                int(self.pages_info['count'])):
                return
            pages -= 1
            page += 1
    return wrapper

class Danbooru(object):
    def __init__(self):
        self.pages_info = None

    @api('post/index.xml', limit=100)
    def posts(self, xml):
        self.pages_info = xml.attrib
        return [Post(x) for x in xml]

    posts_paged = paged(posts)

    @api('/tag/index.xml', limit=100)
    def tags(self, xml):
        # what am i supposed to do with this?
        pass

class AllTags(object):
    '''Uses a sqlite database because otherwise it would eat ~150mb ram'''

    instance = None

    CREATE = 'CREATE TABLE IF NOT EXISTS tags ' \
        '(id INT, name VARCHAR(128), type INT, count INT)'
    INSERT = 'INSERT INTO tags (id, name, type, count) VALUES (?, ?, ?, ?)'

    DB_FILENAME = 'tags.sqlite'

    def __init__(self):
        if not os.path.exists(self.DB_FILENAME):
            self._create_cache()
        
        self.connection = sqlite3.connect(self.DB_FILENAME)
        self.cursor = self.connection.cursor()

        self._types = {}

    def query(self, sql, *args):
        self.cursor.execute(sql, args)
        return self.cursor

    def get_tag(self, name):
        return self.query("SELECT * FROM tags WHERE name=?;", name).fetchone()
    
    def get_tag_type(self, name):
        if name not in self._types:
            row = self.get_tag(name)
            if row:
                self._types[name] = row[2]
        return self._types.get(name, 0)
    
    def _create_cache(self):
        if not os.path.exists("tags.xml"):
            node = request('tag/index.xml', {'limit': 0})
            xml = lxml.etree.ElementTree(node)
            xml.write("tags.xml")
        else:
            xml = lxml.etree.parse("tags.xml")
        
        connection = sqlite3.connect(self.DB_FILENAME)
        cursor = connection.cursor()
        cursor.execute(AllTags.CREATE)
        connection.commit()

        for tag in xml.getroot():
            params = [tag.attrib[n] for n in ('id', 'name', 'type', 'count')]
            cursor.execute(AllTags.INSERT, tuple(params))
        connection.commit()
        connection.close()

    @classmethod
    def get(cls):
        if cls.instance:
            return cls.instance
        cls.instance = cls()
        return cls.instance

class Post(object):
    '''
    <post
    sample_url="http://danbooru.donmai.us/data/(MD5).png" 
    preview_url="http://danbooru.donmai.us/data/preview/(MD5).jpg" 
    preview_width="92"
    parent_id=""
    change="2296870"
    has_notes="false" 
    created_at="Fri Feb 05 23:59:59 -0500 2010" 
    file_size="(BYTES)"
    preview_height="150"
    sample_width="744" 
    rating="e"  
    has_children="false" 
    tags="..." 
    creator_id="102191" 
    sample_height="1208"
    status="active" 
    score="1" 
    id="(ID)" 
    author="(USER)" 
    height="1208" 
    source="(URL)" 
    md5="(MD5)" 
    file_url="http://danbooru.donmai.us/data/(MD5).png"
    width="744"
    has_comments="false"/
    '''
    def __init__(self, node):
        for attr, value in node.attrib.iteritems():
            setattr(self, attr, value)
        
        self._tags_parsed = None
    
    def __repr__(self):
        return (u'<post id=%s size=%sx%s md5=%s tags=%s>' %
                (self.id, self.width, self.height, self.md5, self.tags)
            ).encode('utf-8')

    @property
    def tags_parsed(self):
        if self._tags_parsed:
            return self._tags_parsed
        self._tags_parsed = TagList(self.tags)
        return self._tags_parsed

class TagList(object):
    __slots__ = ['all', 'general', 'artist', 'copyright', 'character']

    def __init__(self, string):
        self.all = []
        self.general = []
        self.artist = []
        self.copyright = []
        self.character = []
        
        alltags = AllTags.get()
        for tag in string.split(' '):
            self.all.append(tag)
            tag_type = alltags.get_tag_type(tag)
            if tag_type is not None:
                getattr(self, TAG_TYPES[tag_type]).append(tag)
            else:
                print("unknown tag type of tag", tag, file=sys.stderr)

def posts(**kwargs):
    return Danbooru().posts(**kwargs)
