# -*- coding: utf-8 -*-

import datetime
import re
import flask
import jinja2
from flask import request
from werkzeug.urls import url_quote_plus
from flaskext.csrf import generate_csrf_token

from app import app, cache

_template_funcs = {}

def template_func(f, name=None):
  _template_funcs[name or f.__name__] = f
  return f


def to_unicode(s):
  if not isinstance(s, basestring):
    s = unicode(s)
  elif not isinstance(s, unicode):
    s = unicode(s, 'utf-8')
  return s


def to_str(s):
  if not isinstance(s, basestring):
    s = unicode(s)
  if isinstance(s, unicode):
    s = s.encode('utf-8')
  return s


def _setup_template(template, **kwds):
  global _template_funcs
  values = {}
  if kwds:
    values.update(kwds)
  values.update(_template_funcs)
  if '.' not in template:
    template = '%s.html' % template
  return template, values


def fetch(template, **kwds):
  template, kwds = _setup_template(template, **kwds)
  flask.current_app.update_template_context(kwds)
  return flask.current_app.jinja_env.get_template(template).render(kwds)


def render(template, **kwds):
  template, kwds = _setup_template(template, **kwds)
  return flask.render_template(template, **kwds)


def render_text(value, mimetype='text/plain', **kwds):
  return flask.current_app.response_class(value, mimetype=mimetype, **kwds)


@app.template_filter()
def yobi(value):
  if not isinstance(value, (int, long)):
    value = value.weekday()
  return u'月火水木金土日祝'[value]


FORMAT_DATE_MAP = {
  'full': '%Y/%m/%d (%a) %H:%M:%S',
  'long': '%Y/%m/%d (%a) %H:%M',
  'short': '%Y/%m/%d %H:%M',
  'date_long': '%Y/%m/%d (%a)',
  'date_short': '%Y/%m/%d',
  'date': '%Y/%m/%d',
  'date_long_jp': u'%Y年%m月%d日(%a)',
  'monthday_long': '%m/%d (%a)',
  'monthday_short': '%m/%d',
  'monthday': '%m/%d',
  'time_long': '%H:%M',
  'time_short': '%H:%M',
  'time': '%H:%M',
  'daytime_long': '%m/%d (%a) %H:%M',
  'daytime_short': '%m/%d %H:%M',
  'daytime': '%m/%d %H:%M',
  'rfc822': '%a, %d %b %Y %H:%M:%S',
  'html5': '%Y-%m-%d %H:%M:%S',
  }

@app.template_filter('date')
def format_date(dt, format=None):
  #from aha coreblog3

  if dt is None:
    return u''

  if not isinstance(dt, datetime.datetime):
    dt = datetime.datetime(dt.year, dt.month, dt.day)
    if not format:
      format = 'date_short'
  
  if not format:
    format = 'short'
  elif 'auto' == format:
    today = datetime.date.today()
    if dt.date() == today:
      format = '%H:%M'
    elif dt.year == today.year:
      format = '%m/%d'
    else:
      format = '%Y/%m/%d'
  
  if format in FORMAT_DATE_MAP:
    format = FORMAT_DATE_MAP[format]
  
  if '%a' in format:
    format = to_unicode(format).replace('%a', yobi(dt))
  return to_unicode(dt.strftime(to_str(format)))


@app.template_filter()
@jinja2.environmentfilter
def nl2br(env, s, arg='<br />'):
  if not s:
    return s
  result = arg.join(to_unicode(s).split(u'\n'))
  if env.autoescape:
    result = jinja2.Markup(result)
  return result


@app.template_filter()
def obfuscate(value, js=False):
  value = to_unicode(value)
  ret = []
  for c in value:
    c = c.encode('utf-8')
    if 2 <= len(c):
      ret.append(c)
    else:
      if js:
        ret.append('%%%s' % c.encode('hex'))
      else:
        ret.append('&#%d;' % ord(c))
  return ''.join(ret)


@template_func
@jinja2.environmentfunction
def mail_tag(env, mail, encode=None, **kwds):
  
  options = {
    'cc':      None,
    'bcc':     None,
    'subject': None,
    'body':    None,
    }
  options.update(kwds)
  
  name = mail
  extras = []
  htmloptions = []
  for key, value in options.iteritems():
    if not value:
      continue
    elif 'cc' == key or 'bcc' == key:
      value = value.strip()
      if value:
        value = url_quote_plus(value)
        value = value.replace('+', '%20')
        value = value.replace('%40', '@')
        value = value.replace('%2C', ',')
        extras.append('%s=%s' % (key, value))
    elif 'body' == key or 'subject' == key:
      value = to_str(value).strip()
      if value:
        value = url_quote_plus(value)
        value = value.replace('+', '%20')
        extras.append('%s=%s' % (key, value))
    elif 'name' == key:
      name = value
    else:
      htmloptions.append('%s=%s' % (jinja2.escape(key), jinja2.escape(value)))
  
  extras = '&'.join(extras)
  if extras:
    extras = '?' + extras
  htmloptions = ' '.join(htmloptions)
  
  if encode is None:
    result = '<a href="mailto:%s%s" %s>%s</a>' % (mail, extras, htmloptions, name)
  
  else:
    mailto = obfuscate('mailto:%s' % mail)
    atag = '<a href="%s%s" %s>%s</a>' % (mailto, extras, htmloptions, obfuscate(name))
    if 'js' != encode:
      result = atag
    
    else:
      tmp = obfuscate('document.write(\'%s\');' % atag, js=True)
      result = '<script type="text/javascript">eval(unescape(\'%s\'));</script>' % tmp
  
  if env.autoescape:
    result = jinja2.Markup(result)
  return result


_ustring_re = re.compile(u'([\u0080-\uffff])')

@app.template_filter()
@jinja2.environmentfilter
def escape_js(env, s, quote_double_quotes=False):
  def fix(match):
    return r"\u%04x" % ord(match.group(1))
  if type(s) == str:
    s = s.decode('utf-8')
  elif type(s) != unicode:
    raise TypeError, s
  s = s.replace('\\', '\\\\')
  s = s.replace('\r', '\\r')
  s = s.replace('\n', '\\n')
  s = s.replace('\t', '\\t')
  s = s.replace("'", "\\'")
  if quote_double_quotes:
    s = s.replace('"', '&quot;')
  return str(_ustring_re.sub(fix, s))


@template_func
@jinja2.environmentfunction
def link_options(env, **kwds):
  confirm = kwds.pop('confirm', None)
  post = kwds.pop('post', None)
  popup = kwds.pop('popup', None)
  
  def _popup_js(p, u='this.href'):
    if isinstance(p, list):
      if 2 <= len(p):
        return "var w=window.open(%s,'%s','%s');w.focus();" % (u, p[0], p[1])
      else:
        return "var w=window.open(%s,'%s');w.focus();" % (u, p[0])
    else:
      return "var w=window.open(%s);w.focus();" % (u,)
  
  def _post_js():
    return ''.join([
      "var f = document.createElement('form'); f.style.display = 'none';"
      "this.parentNode.appendChild(f); f.method = 'post'; f.action = this.href;",
      "var m = document.createElement('input'); m.setAttribute('type', 'hidden');",
      "m.setAttribute('name', '_csrf'); m.setAttribute('value', '%s'); f.appendChild(m);" % (
        generate_csrf_token(),),
      "f.submit();",
      ])
  
  def _confirm_js(msg):
    return "confirm('%s')" % escape_js(env, msg)
  
  onclick = kwds.get('onclick', '')
  if popup and post:
    raise ValueError('You can not use "popup" and "post" in the same link.')
  elif confirm and popup:
    kwds['onclick'] = onclick + (";if(%s){%s};return false;" % (_confirm_js(confirm), _popup_js(popup)))
  elif confirm and post:
    kwds['onclick'] = onclick + (";if(%s){%s};return false;" % (_confirm_js(confirm), _post_js()))
  elif confirm:
    if onclick:
      kwds['onclick'] = "if(%s){return %s}else{return false;}" % (_confirm_js(confirm), onclick)
    else:
      kwds['onclick'] = "return %s;" % _confirm_js(confirm)
  elif post:
    kwds['onclick'] = "%s return false;" % _post_js()
  elif popup:
    kwds['onclick'] = "%s return false;" % _popup_js(popup)
  
  return html_options(**kwds)


@template_func
def html_options(**kwds):
  if not kwds:
    return u''
  opts = []
  for n, v in kwds.items():
    opts.append(u'%s="%s"' % (jinja2.escape(n), jinja2.escape(v)))
  return jinja2.Markup(u' '.join(opts))


@app.template_filter('limit')
def truncate_by_width(s, num, end='...'):
  if not s:
    return s
  length = int(num)
  if length <= 0:
    return u''
  s = to_unicode(s)
  if num >= len(s):
    return s
  return u''.join([s[:num], end])


@app.template_filter('number')
def format_number(s):
  if isinstance(s, basestring):
    s = long(s)
  if isinstance(s, (int, long)):
    s = '%d' % s
  else:
    s = '%f' % s
  slen = len(s)
  return ','.join(reversed([s[max(slen - (i + 3), 0):max(slen - i, 0)]
    for i in range(0, slen + ((3 - (slen % 3)) % 3), 3)]))


@template_func
@jinja2.environmentfunction
def link_to(env, name, path, **kwds):
  options_str = ' %s ' % link_options(env, **kwds) if kwds else u''
  if not path.startswith('/') and not path.startswith('http'):
    path = url(path)
  result = '<a href="%s"%s>%s</a>' % (jinja2.escape(path),
    options_str, jinja2.escape(name))
  if env.autoescape:
    result = jinja2.Markup(result)
  return result


@template_func
def url(endpoint, **values):
  external = values.pop('_external', False)
  if endpoint.startswith('/'):
    ret = endpoint
  else:
    ret = flask.url_for(endpoint, **values)
  if external:
    scheme = 'https' if flask.request.is_secure else 'http'
    ret = '%s://%s%s' % (scheme, request.host, ret)
  return ret


@template_func
@jinja2.environmentfunction
def csrf_tag(env):
  result = u'<input type="hidden" name="_csrf" value="%s" />' % generate_csrf_token()
  if env.autoescape:
    result = jinja2.Markup(result)
  return result


@template_func
@jinja2.environmentfunction
def form_tag(env, path=None, **kwds):
  kwds.setdefault('method', 'post')
  options = html_options(**kwds)
  if not path:
    path = request.path
  result = u'<form action="%s" %s >%s' % (path, options, csrf_tag(env))
  if kwds['method'] in ('delete', 'put'):
    result += ('<input type="hidden" name="_method" value="%s" />' % kwds['method'])
  if env.autoescape:
    result = jinja2.Markup(result)
  return result


@app.before_request
def set_current_datetime():
  flask.g.current_time = datetime.datetime.now()


def get_current_datetime():
  return flask.g.current_time


@app.context_processor
def inject_globals():
  import model
  return dict(
    model=model,
    current_day=get_current_datetime().date(),
    current_time=get_current_datetime(),
    )


def get_pagenation(current, total, page_size, param_name='start', maxpages=10):
  """
  A helper function to make list of pagenation
    current   : the item number of current page
    max     : total number of items
    page_size : item count in each page
  """
  #from aha coreblog3
  pages = []
  if total > page_size:
    current_p = 0
    lstart = 0
    lend = total
    dd = 0
    showskip = False
    if total/page_size > maxpages:
      showskip = True
      lstart = (current/page_size-(maxpages/2))*page_size
      if lstart<0:
        lstart = 0
        showskip = False
      if lstart+maxpages*page_size >= total:
        lstart = (total/page_size-maxpages)*page_size
        showskip = False
      lend = ((lstart+(page_size*maxpages))/page_size)*page_size
      dd = lstart/page_size
    for n, p in enumerate(range(lstart, lend, page_size)):
      if p <= current < p+page_size:
        pages.append( ('current', str(n+1+dd)) )
        current_p = p
      else:
        pages.append( ('?start='+str(p), str(n+1+dd)) )
    if current_p >= page_size:
      if showskip:
        pos = max(current_p-(page_size*maxpages), 0)
        pages = [ ('?start=0', '1..') ]+pages
        pages = [ ('?start='+str(pos), '<<') ]+pages
      else:
        pages = [ ('?start='+str(current_p-page_size), '<') ]+pages
    else:
      pages = [ ('', '<<') ]+pages
    if current_p < total-page_size:
      if showskip:
        pos = min(current_p+(page_size*maxpages), 
            (total/page_size)*page_size)
        pages += [ ('?start='+str((total/page_size)*page_size),
              '..%s' % (total/page_size)) ]
        pages += [ ('?start='+str(pos), '>>') ]
      else:
        pages += [ ('?%s=%s'%(param_name, current_p+page_size), '>') ]
    else:
      pages += [ ('', '>>') ]
  return pages


def abort_if(cond, code=404, *args, **kwds):
  if cond:
    flask.abort(code, *args, **kwds)


def urlfetch(url, params=None, timeout=10, cache_lifetime=60):
  import urllib2
  import socket
  from werkzeug.urls import url_encode
  query = url_encode(params, sort=True) if params else ''
  url = url + '?' + query
  
  key = 'helpers.urlfetch.%s' % url
  ret = cache.get(key)
  if ret:
    return ret
  
  old_timeout = socket.getdefaulttimeout()
  try:
    print url
    socket.setdefaulttimeout(timeout)
    ret = urllib2.urlopen(url).read()
    cache.set(key, ret, cache_lifetime)
    return ret
  except urllib2.URLError, ex:
    print ex
    return None
  finally:
    socket.setdefaulttimeout(old_timeout)
