#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = u'Rintcius Blok'
SITENAME = u'Blok blogs'
SITEURL = ''

TIMEZONE = 'Europe/Paris'

DEFAULT_LANG = u'en'

# Blogroll
LINKS =  (('webservices.io', 'http://webservices.io'),)

# Social widget
SOCIAL = (('twitter', 'http://twitter.com/rintcius'),
          ('github', 'http://github.com/rintcius'))

FILES_TO_COPY = (('extra/CNAME', 'CNAME'),)

DEFAULT_PAGINATION = 10

THEME = 'io.svc.simple'

PAGE_URL = 'page/{slug}.html'
PAGE_SAVE_AS = 'page/{slug}.html'
PAGE_LANG_URL = 'page/{slug}-{lang}.html'
PAGE_LANG_SAVE_AS = 'page/{slug}-{lang}.html'

ARTICLE_URL = '{slug}.html'
ARTICLE_SAVE_AS = '{slug}.html'
ARTICLE_LANG_URL = '{slug}-{lang}.html'
ARTICLE_LANG_SAVE_AS = '{slug}-{lang}.html'

DISQUS_SITENAME = 'rintcius'
TWITTER_USERNAME = 'rintcius'

from pelican.plugins import related_posts
PLUGINS = [related_posts]