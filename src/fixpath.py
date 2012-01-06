# -*- coding: utf-8 -*-

import os
import sys

LIB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if LIB_PATH not in sys.path:
  sys.path.insert(0, LIB_PATH)
