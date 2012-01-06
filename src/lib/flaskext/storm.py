# -*- coding: utf-8 -*-

from __future__ import with_statement, absolute_import
import datetime
import functools
import flask
from storm.locals import create_database, Store
from storm.properties import Property, Int, Float, RawStr
from storm.properties import Chars, Unicode, DateTime, Date


class Error(Exception):
  """Base datastore error type."""


class BadValueError(Error):
  """Raised by validation when a property value or filter value is invalid."""


class DuplicatePropertyError(Error):
  """Raised when a property is duplicated in a model definition."""


class ReservedWordError(Error):
  """Raised when a property is defined for a reserved word."""


def connection():
  """Returns database connection."""
  try:
    if not flask.g.db:
      raise AttributeError()
  except (KeyError, AttributeError):
    flask.g.db = Store(create_database(flask.current_app.config['STORM_DATABASE_URI']))
  return flask.g.db


def close_connection(response=None):
  """Close database connection."""
  try:
    if flask.g.db:
      tmp = flask.g.db
      flask.g.db = None
      tmp.rollback()
      tmp.close()
  except (KeyError, AttributeError):
    pass
  return response


def use_storm(app):
  """Setup Storm."""
  app.after_request(close_connection)

  #アプリが例外を投げるとafter_request呼ばれないので
  #処理の開始前にもコネクションのロールバックをさせることで
  #デッドロックを防止する。念のため、シグナルもキャッチして同様に処理する。
  app.before_request(close_connection)
  
  from flask import request_finished, got_request_exception
  
  def request_finished_handler(sender, response):
    close_connection(response)
  request_finished.connect(request_finished_handler, app)
  
  def got_request_exception_handler(sender, exception):
    close_connection()
  got_request_exception.connect(got_request_exception_handler, app)


def rollback(func):
  @functools.wraps(func)
  def _wrapper(*args, **kwds):
    try:
      return func(*args, **kwds)
    finally:
      if flask.g.db:
        flask.g.db.rollback()
  return _wrapper


class PropertiedClass(type):

  def __init__(cls, name, bases, dct, map_kind=True):
    super(PropertiedClass, cls).__init__(name, bases, dct)
    _initialize_properties(cls, name, bases, dct)


_RESERVED_PROPERTY_NAMES = ('properties',)

def _initialize_properties(model_class, name, bases, dct):
  props = {}
  for attr_name in dct.keys():
    attr = dct[attr_name]
    if isinstance(attr, Property):
      assert attr_name not in _RESERVED_PROPERTY_NAMES
      if attr_name in props:
        raise DuplicatePropertyError('Duplicate property: %s' % attr_name)
      props[attr_name] = attr
  model_class.properties = props


def auto_now_add(*props):
  for prop in props:
    prop.__storm_ext_auto_now_add__ = True


def auto_now(*props):
  for prop in props:
    prop.__storm_ext_auto_now__ = True


def required(*props):
  for prop in props:
    prop.__storm_ext_required__ = True


def protected(*props):
  for prop in props:
    prop.__storm_ext_protected__ = True


class Model(object):

  __metaclass__ = PropertiedClass

  properties = None

  def __storm_pre_flush__(self):
    for prop_name, prop in self.properties.iteritems():
      if getattr(prop, '__storm_ext_required__', False):
        if prop.__get__(self) is None:
          raise BadValueError('Property %s is required' %
            prop._get_column(self.__class__).name)
      if getattr(prop, '__storm_ext_auto_now_add__', False):
        if not prop.__get__(self):
          prop.__set__(self, datetime.datetime.now())
      elif getattr(prop, '__storm_ext_auto_now__', False):
        prop.__set__(self, datetime.datetime.now())
    self.validate()

  def __init__(self, **kwds):
    self.apply(**kwds)

  def validate(self):
    pass

  def apply(self, **kwds):
    #変更できない項目への変更を防ぐ
    #エラーの場合は他のプロパティも更新されないよう、
    #最初に判定しておく
    for k, v in kwds.iteritems():
      if k and k in self.properties:
        p = self.properties[k]
        assert not getattr(p, '__storm_ext_protected__', False)
    
    for k, v in kwds.iteritems():
      
      if k and k in self.properties:
        p = self.properties[k]
        
        if isinstance(p, Int):
          if isinstance(v, basestring):
            if not v:
              v = None
            else:
              v = long(v)
          
        elif isinstance(p, Float):
          if isinstance(v, basestring):
            if not v:
              v = None
            else:
              v = float(v)
          
        elif isinstance(p, (Chars, Unicode)):
          if not v:
            v = None
          elif not isinstance(v, unicode):
            v = unicode(v, 'utf-8')
          
        elif isinstance(p, RawStr):
          if not v:
            v = None
          
        elif isinstance(p, DateTime):
          if isinstance(v, basestring):
            if not v:
              v = None
            else:
              v = datetime.datetime.strptime(v, '%Y/%m/%d %H:$M:%S')
          
        elif isinstance(p, Date):
          if isinstance(v, basestring):
            if not v:
              v = None
            else:
              v = datetime.datetime.strptime(v, '%Y/%m/%d').date()
        
        p.__set__(self, v)
