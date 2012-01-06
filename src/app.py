# -*- coding: utf-8 -*-

import sys
import os
import logging
import flask
from werkzeug import cached_property, ImmutableDict
from jinja_loader import MemoryBytecodeCache, FileSystemLoaderEx


class Server(flask.Flask):

  jinja_options = ImmutableDict(flask.Flask.jinja_options.items() +
    [('bytecode_cache', MemoryBytecodeCache())])

  @cached_property
  def jinja_loader(self):
    return FileSystemLoaderEx(os.path.join(self.root_path, 'templates'))


Server.request_class.is_behind_proxy = True


def setup_app(app):
  _app_path = os.path.abspath(__file__)
  if ':\\' in _app_path:
    app.config.from_object('config.Local')
  elif '/prod/' in _app_path:
    app.config.from_object('config.Product')
  else:
    app.config.from_object('config.Develop')
  app.url_map.strict_slashes = False


app = Server(__name__)
setup_app(app)

from flaskext.cache import Cache
cache = Cache(app)

from flaskext.storm import use_storm
use_storm(app)


if app.debug:
  from storm.tracer import debug as storm_debug
  storm_debug(True, stream=sys.stdout)
else:
  from logging import StreamHandler
  handler = StreamHandler(sys.stderr)
  handler.setLevel(logging.INFO)
  app.logger.addHandler(handler)
  @app.after_request
  def flush_log(response):
    handler.flush()
    return response
