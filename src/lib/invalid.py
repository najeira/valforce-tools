# -*- coding: utf-8 -*-

import re
import datetime as datetime_module

_datere = r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
_timere = r'(?:[01]?[0-9]|2[0-3]):[0-5][0-9](?::[0-5][0-9])?'
year_re = re.compile(r'\d{4}')
ansi_date_re = re.compile('^%s$' % _datere)
ansi_time_re = re.compile('^%s$' % _timere)
ansi_datetime_re = re.compile('^%s %s$' % (_datere, _timere))
email_re = re.compile(r'^([^@\s]+)@((?:[-a-z0-9]+\.)+[a-z]{2,6})$', re.IGNORECASE)
integer_re = re.compile(r'^-?\d+$')
float_re = re.compile(r'^(-?\d+\.\d+|\.\d+)$')
ip4_re = re.compile(r'^(25[0-5]|2[0-4]\d|[0-1]?\d?\d)(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}$')
phone_re = re.compile(r'^\d{2,5}-?\d{1,4}-?\d{3,5}$')
post_re = re.compile(r'^\d{3}-?\d{4}$')
slug_re = re.compile(r'^[-\w]+$')
url_re = re.compile(r'^https?://\S+$')
domain_re = re.compile(r'^(\w+\.)\w+\.\w{2,6}$')


def empty(value, **options):
  return not value


def length(value, min=None, max=None, eq=None, **options):
  if empty(value, **options):
    return False
  len_str = len(value)
  if min and len_str < min:
    return True
  if max and len_str > max:
    return True
  if eq and len_str != eq:
    return True
  return False


def integer(value, **options):
  if empty(value, **options):
    return False
  return integer_re.search(value) is None


def numeric(value, **options):
  if empty(value, **options):
    return False
  return integer(value, **options) or float_re.search(value) is None


def year(value, **options):
  if empty(value, **options):
    return False
  return year_re.search(value) is None


def date(value, **options):
  if empty(value, **options):
    return False
  return ansi_date_re.search(value) is None


def time(value, **options):
  if empty(value, **options):
    return False
  return ansi_time_re.search(value) is None


def datetime(value, **options):
  if empty(value, **options):
    return False
  return ansi_datetime_re.search(value) is None


def phone(value, **options):
  if empty(value, **options):
    return False
  if 10 > len(value.replace('-', '')):
    return True
  return phone_re.search(value) is None


tel = phone


def post(value, **options):
  if empty(value, **options):
    return False
  return post_re.search(value) is None


def url(value, **options):
  if empty(value, **options):
    return False
  return url_re.search(value) is None


def mail(value, **options):
  if empty(value, **options):
    return False
  return email_re.search(value) is None


def domain(value, **options):
  if empty(value, **options):
    return False
  if 'localhost' == value:
    return False
  return domain_re.search(value) is None


def slug(value, **options):
  if empty(value, **options):
    return False
  return slug_re.search(value) is None


DAY_COUNTS = (31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)

def check_date(year, month, day):
  if month < 1 or 12 < month:
    return True
  if day < 1 or DAY_COUNTS[month - 1] < day:
    return True
  if 2 != month or day <= 28:
    return False
  return 0 == (year % 4) and 0 != (year % 100) or 0 == (year % 400)


def is_past_date(date):
  if not date:
    return True
  return date <= datetime_module.date.today()


def is_future_date(date):
  if not date:
    return True
  return date >= datetime_module.date.today()


def is_future_datetime(datetme):
  if not datetme:
    return True
  from dateutil import jst, jst_now
  return jst(datetme) >= jst_now()


def is_recent_date(date):
  if not date:
    return True
  return 1900 <= date.year
