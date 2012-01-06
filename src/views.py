# -*- coding: utf-8 -*-

import re

from flask import request, current_app

from app import app
import model
from helpers import render, render_text, abort_if, urlfetch

logger = app.logger


@app.route('/')
def index():
  """ホーム"""
  
  #新着のリプレイ
  matches = model.Match.all(limit=10)
  
  #TODO: 1ヶ月以内のStatistics
  #キャラ別の使用数、勝率？
  
  game_servers = fetch_game_servers() or ''
  
  return render('index.html', matches=matches, game_servers=game_servers)


GAME_SERVERS_RE = re.compile(u'%s.*?%s' % (
  re.escape(u'<TABLE BORDER=1 CELLPADDING=5 CELLSPACING=0><TR><TH>接続先</TH><TH>バージョン</TH><TH>接続人数</TH></TR>'),
  re.escape(u'</TR></TABLE>'),
))

def fetch_game_servers():
  html = urlfetch('http://yumesoft.net/')
  if html:
    if not isinstance(html, unicode):
      html = html.decode('shift_jis', 'replace')
    match = GAME_SERVERS_RE.search(html)
    if match:
      return match.group(0)


@app.route('/search')
def search():
  """検索"""
  
  params = dict(
    char=request.args.get('char') or None,
    win_lose=request.args.get('win_lose') or None,
    stage=request.args.get('stage') or None,
    span=request.args.get('span') or None,
    version=request.args.get('version') or None,
  )
  matches = None
  if len(request.args):
    matches = model.Match.search(
      page=int(request.args.get('page') or 1), **params)
  
  return render('search.html', matches=matches, params=params)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
  """アップロード"""
  
  if 'POST' != request.method:
    return render('upload.html')
  
  file = request.files['Filedata']
  if not file:
    return render_text(u'error_nofile', status=400)
  
  try:
    source = file.stream.read()
  except AttributeError:
    source = file.stream.getvalue()
  
  #最大サイズ
  if 1024 * 512 < len(source):
    return render_text(u'error_size', status=413)
  
  author = request.remote_addr
  
  #データ登録
  try:
    model.Match.get_or_insert(source, author=author)
  except model.ParseError, ex:
    logger.warn(ex)
    return render_text(u'error_data', status=415)
  except Exception, ex:
    logger.warn(ex)
    return render_text(u'error_data', status=415)
  
  return render_text(u'ok')


@app.route('/match/<int:id>')
def match(id):
  match = model.Match.get_by_id(id)
  abort_if(not match)
  return render('match.html', match=match)


@app.route('/match/<int:id>/download')
def match_download(id):
  match = model.Match.get_by_id(id)
  match_data = model.MatchData.get_by_id(id)
  abort_if(not match)
  abort_if(not match_data)
  
  data = match_data.raw_data
  abort_if(not data)
  print len(data)
  
  from werkzeug import Headers
  import time
  
  headers = Headers()
  headers.add('Content-Disposition', 'attachment', filename=match.filename)
  
  rv = current_app.response_class(
    data,
    mimetype='application/octet-stream',
    headers=headers,
    direct_passthrough=True,
    )
  rv.cache_control.public = True
  rv.cache_control.max_age = 86400
  rv.expires = int(time.time() + 86400)
  
  return rv
