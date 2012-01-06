# -*- coding: utf-8 -*-

import os

_passwd = 'root'
_fp = None
try:
  _fp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'passwd'), 'rb')
  _passwd = _fp.read()
finally:
  if _fp:
    _fp.close()


class _Config(object):
  SECRET_KEY = 'ldoekduvkjfaslkjsfadlkj'
  SESSION_COOKIE_NAME = 's'
  CACHE_TYPE = 'simple'
  CACHE_MEMCACHED_SERVERS = ['127.0.0.1:11211']


class Product(_Config):
  STORM_DATABASE_URI = 'mysql://%s@localhost/valforce_prod' % _passwd
  CACHE_TYPE = 'memcached'


class Local(_Config):
  DEBUG = True
  STORM_DATABASE_URI = 'mysql://%s@localhost/valforce_dev' % _passwd


class Test(_Config):
  TESTING = True
  STORM_DATABASE_URI = 'mysql://%s@localhost/valforce_test' % _passwd

