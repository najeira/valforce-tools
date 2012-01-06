# -*- coding: utf-8 -*-

import re
from jinja2 import FileSystemLoader, BytecodeCache


class FileSystemLoaderEx(FileSystemLoader):

  _strip_extentions = ('.html', '.htm', '.xml', '.xhtml')

  def get_source(self, environment, template):
    source, filename, uptodate = super(
      FileSystemLoaderEx, self).get_source(environment, template)
    if filename.endswith(self._strip_extentions):
      source = _strip_template(source)
    return source, filename, uptodate


class MemoryBytecodeCache(BytecodeCache):

  def __init__(self):
    self.cache = {}

  def load_bytecode(self, bucket):
    if bucket.key in self.cache:
      bucket.bytecode_from_string(self.cache[bucket.key])

  def dump_bytecode(self, bucket):
    self.cache[bucket.key] = bucket.bytecode_to_string()

  def clear(self):
    self.cache = {}


_content_repl_script_re = re.compile('(</script.*?>|^)(.*?)(<script.*?>|$)',
  re.IGNORECASE | re.DOTALL)
_content_repl_textarea_re = re.compile('(</textarea.*?>|^)(.*?)(<textarea.*?>|$)',
  re.IGNORECASE | re.DOTALL)
_content_repl_tag_re = re.compile('(>|^)(.*?)(<|$)', re.DOTALL)
_content_repl_space_re = re.compile(r'[\t\s]*[\r\n]+[\t\s]*', re.MULTILINE)


def _strip_template(source):
  return _content_repl_script_re.sub(_content_repl_func1, source)


def _content_repl_func1(matchobj):
  start = matchobj.group(1)
  target = matchobj.group(2)
  end = matchobj.group(3)
  target = _content_repl_textarea_re.sub(_content_repl_func2, target)
  return start + target + end


def _content_repl_func2(matchobj):
  start = matchobj.group(1)
  target = matchobj.group(2)
  end = matchobj.group(3)
  target = _content_repl_tag_re.sub(_content_repl_func3, target)
  return start + target + end


def _content_repl_func3(matchobj):
  start = matchobj.group(1)
  target = matchobj.group(2)
  end = matchobj.group(3)
  target = _content_repl_space_re.sub('', target)
  return start + target + end
