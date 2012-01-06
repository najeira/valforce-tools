# -*- coding: utf-8 -*-

import os
import datetime
import zlib
import cStringIO
from hashlib import sha1
from flaskext.storm import Model, auto_now_add, required, connection, close_connection
from storm.properties import Int, Unicode, DateTime, RawStr
from storm.expr import And, Or, Desc
from storm.references import Reference


class Error(Exception):
  """"""


class ParseError(Error):
  """"""


def init():
  """データベースを初期化します。
  この関数を呼び出すと、データベースのデータは削除されます。
  """
  executescript('schema.sql')


def fixture():
  """fixtureを読み込んで実行します。"""
  executescript('fixture.sql')


def executescript(filename):
  """指定されたファイル名のSQLスクリプトを読み込んで実行します。"""
  conn = None
  try:
    conn = connection()
    conn.execute(_read_file(filename), noresult=True)
    conn.commit()
  except:
    if conn:
      conn.rollback()
    raise
  finally:
    close_connection()


def _read_file(filename):
  """指定されたファイル名のSQLスクリプトを読み込んで返します。"""
  f = None
  try:
    f = open(os.path.join(os.path.abspath(os.path.dirname(__file__)),
      'etc', filename), 'rb')
    return f.read()
  finally:
    if f:
      f.close()


_DAY_COUNTS = [31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

def month_last_day(year, month):
  """指定された年と月の、最後の日にちを取得します。"""
  if 2 != month:
    return _DAY_COUNTS[month - 1]
  elif 0 == (year % 4) and 0 != (year % 100) or 0 == (year % 400):
    return 29
  else:
    return 28


### models


class Match(Model):
  
  __storm_table__ = 'match'
  
  RESULT_HOME = 1
  RESULT_AWAY = 2
  RESULT_DRAW = 3
  
  RESULTS = [
    (RESULT_HOME, u'1P勝利'),
    (RESULT_AWAY, u'2P勝利'),
    (RESULT_DRAW, u'引き分け'),
  ]
  RESULT_MAP = dict([(_[0], _[1]) for _ in  RESULTS])
  
  CHARACTERS = [
    ('AI', u'神凪アイ'),
    ('NA', u'黒羽ナガレ'),
    ('ME', u'宝鏡メイ'),
    ('SE', u'斑鳩セツナ'),
    ('MA', u'六堂マリア'),
    ('AY', u'月影アヤカ'),
    ('RE', u'春風レン'),
    ('EL', u'美澤エレナ'),
  ]
  CHARACTER_MAP = dict([(_[0], _[1]) for _ in  CHARACTERS])
  
  STAGES = [
    'MILITARY TRAIN',
    'SECRET SANCTUARY',
    'MIDNIGHT CITY',
    'SPACE ELEVATOR',
    'TROPICAL BEACH',
    'AIRCRAFT CARRIER',
    'SHINTO SHRINE',
    'ANCIENT RUINS',
  ]
  
  VERSIONS = ['2.03', '2.04']
  
  id = Int(primary=True)
  
  #プレイヤ1キャラ
  home = Unicode()
  
  @property
  def home_name(self):
    return self.CHARACTER_MAP.get(self.home)
  
  #プレイヤ2キャラ
  away = Unicode()
  
  @property
  def away_name(self):
    return self.CHARACTER_MAP.get(self.away)
  
  #プレイヤ1名前
  home_player = Unicode()
  
  #プレイヤ2名前
  away_player = Unicode()
  
  #ステージ
  stage = Unicode()
  
  #勝敗
  result = Int()
  
  @property
  def result_name(self):
    return self.RESULTS.get(self.result)
  
  #バージョン
  version = Unicode()
  
  #ハッシュ値
  etag = Unicode()
  
  #アップロード者
  author = Unicode()
  
  #パスコード
  #passcode = Unicode()
  
  #試合日時
  created_at = DateTime()
  
  #アップロード日時
  uploaded_at = DateTime()
  
  required(home, away, home_player, away_player, stage, result, version,
    etag, author, created_at)
  
  auto_now_add(uploaded_at)
  
  @classmethod
  def get_by_id(cls, id):
    return connection().get(cls, id)
  
  @classmethod
  def get_by_etag(cls, value):
    return connection().find(cls,
      cls.etag == (value if isinstance(value, unicode) else value.decode('utf-8'))
      ).config(limit=1).any()
  
  @classmethod
  def get_or_insert(cls, source, **kwds):
    try:
      params = cls.parse(source)
    except Exception:
      raise ParseError()
    
    db = connection()
    obj = cls.get_by_etag(params['etag'])
    if obj:
      return obj
    
    obj = cls()
    obj.apply(**kwds)
    obj.apply(**params)
    db.add(obj)
    
    match_data = MatchData()
    match_data.match = obj
    match_data.raw_data = source
    db.add(match_data)
    
    db.commit()
    return obj
  
  @classmethod
  def parse(cls, source):
    buf = cStringIO.StringIO(source)
    try:
      params = {}
      for s in buf:
        if not s.startswith('#'):
          break
        
        k, v = s.split('=', 1)
        k = k[1:]
        v = v.rstrip('\r\n')
        
        if 'date' == k:
          k = 'created_at'
          v = datetime.datetime.strptime(v, '%Y/%m/%d %H:%M:%S')
        elif '1,name' == k:
          k = 'home_player'
        elif '2,name' == k:
          k = 'away_player'
        elif '1,character' == k:
          k = 'home'
        elif '2,character' == k:
          k = 'away'
        
        params[k] = v
      
      for k in ['created_at', 'home_player', 'away_player',
        'home', 'away', 'winner', 'loser']:
        assert k in params, k
      
      if params['winner'] == params['loser']:
        #プレイヤーが同じだと勝敗が区別できない
        params['result'] = None # Unknown
      elif params['winner'] == params['home_player']:
        params['result'] = cls.RESULT_HOME
      elif params['winner'] == params['away_player']:
        params['result'] = cls.RESULT_AWAY
      else:
        raise NotImplementedError()
      
      params['etag'] = sha1(source).hexdigest()
      
      return params
      
    finally:
      if buf:
        buf.close()
  
  @classmethod
  def all(cls, page=1, limit=25):
    """全ての試合を取得します。"""
    q = connection().find(cls)
    q.order_by(Desc(cls.created_at))
    return cls.build_pager_params(q, page, limit)
  
  @classmethod
  def search(cls, char=None, win_lose=None, stage=None, span=None,
    version=None, page=1, limit=25):
    """試合を取得します。"""
    
    exp = []
    
    if span:
      from helpers import get_current_datetime
      exp.append(cls.created_at >= get_current_datetime() - datetime.timedelta(days=int(span)))
    
    if stage:
      exp.append(cls.stage == stage)
    
    if version:
      exp.append(cls.version == version)
    
    if win_lose:
      assert char
      win_lose = int(win_lose)
      if 1 == win_lose:
        exp.append(
          Or(
            And(cls.home == char, cls.result == cls.RESULT_HOME),
            And(cls.away == char, cls.result == cls.RESULT_AWAY),
          )
        )
      elif 2 == win_lose:
        exp.append(
          Or(
            And(cls.home == char, cls.result == cls.RESULT_AWAY),
            And(cls.away == char, cls.result == cls.RESULT_HOME),
          )
        )
      else:
        raise ValueError()
      
    elif char:
      exp.append(Or(cls.home == char, cls.away == char))
    
    q = connection().find(cls, *exp)
    q.order_by(Desc(cls.created_at))
    return cls.build_pager_params(q, page, limit)
  
  @classmethod
  def build_pager_params(cls, query, page, limit):
    total = query.count()
    offset = (page - 1) * limit
    result = list(query.config(offset=offset, limit=limit))
    start = offset + 1
    end = start + len(result) - 1
    has_next = total > end
    return {
      'page': page,
      'total': total,
      'result': result,
      'start': start,
      'end': end,
      'limit': limit,
      'has_next': has_next,
      'has_result': len(result),
      }
  
  @property
  def filename(self):
    #2011-04-04 23-02-34(RE vs EL)
    return '%s(%s vs %s).rep' % (self.created_at, self.home, self.away)
  
  @property
  def is_win_home(self):
    return self.RESULT_HOME == self.result
  
  @property
  def is_win_away(self):
    return self.RESULT_AWAY == self.result


class MatchData(Model):
  
  __storm_table__ = 'match_data'
  
  match_id = Int(primary=True)
  match = Reference(match_id, Match.id)
  
  #リプレイデータ
  data = RawStr()
  
  def _raw_data_get(self):
    if not self.data:
      return None
    return zlib.decompress(self.data)
  
  def _raw_data_set(self, value):
    self.data = zlib.compress(value)
  
  raw_data = property(_raw_data_get, _raw_data_set)
  
  del _raw_data_get, _raw_data_set
  
  @classmethod
  def get_by_id(cls, id):
    return connection().get(cls, id)
