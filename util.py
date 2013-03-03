from flask import flash, g, redirect
from functools import wraps
import os

def flashy(m, f, u):
    flash(m, f)
    return redirect(u)

def reqLogin(f):
    @wraps(f)
    def _wrapped(*args, **kwargs):
        if g.user is None: return redirect('/')
        return f(*args, **kwargs)
    return _wrapped

def reqLevel(lvl):
    def _wrap(f):
        @wraps(f)
        def _wrapped(*args, **kwargs):
            if g.user is None or not g.user.level >= lvl:
                return redirect('/')
            return f(*args, **kwargs)
        return _wrapped
    return _wrap
