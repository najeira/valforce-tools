# -*- coding: utf-8 -*-
"""
    flaskext.csrf
    ~~~~~~~~~~~~~

    A small Flask extension for adding CSRF protection.

    :copyright: (c) 2010 by Steve Losh.
    :license: MIT, see LICENSE for more details.
"""

from uuid import uuid4
from flask import abort, request, session, g
from werkzeug.routing import NotFound


_exempt_views = []

def csrf_exempt(view):
    _exempt_views.append(view)
    return view

def generate_csrf_token():
    if '_csrf' not in session:
        session['_csrf'] = str(uuid4())[:8]
    return session['_csrf']

def csrf(app, on_csrf=None):
    @app.before_request
    def _csrf_check_exemptions():
        try:
            dest = app.view_functions.get(request.endpoint)
            g._csrf_exempt = dest in _exempt_views
        except NotFound:
            g._csrf_exempt = False
    
    @app.before_request
    def _csrf_protect():
        if not g._csrf_exempt:
            if request.method == "POST":
                csrf_token = session.pop('_csrf', None)
                if not csrf_token or csrf_token != request.form.get('_csrf'):
                    if on_csrf:
                        on_csrf(*app.match_request())
                    abort(400)
    
    app.jinja_env.globals['_csrf'] = generate_csrf_token

