# danbooru.py

A python danbooru interface. Interesting features:

 - Distinction of tag types - by downloading the complete list of tags, then caching it in a sqlite database
 - "paged" iterators - given the parameters `start` (defaults to 0), `pages` (defaults to -1, all pages) and `limit` (per-page, defaults to 100 on posts), turn any paged danbooru api request into a single `for` loop.

This is experimental code, not aimed at end users yet.
