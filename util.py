from flask import flash, g, redirect
from functools import wraps
import os
from datetime import datetime

group_key = {
    20: "regular",
    30: "donator",
    40: "contributor",
    41: "mapdev",
    42: "betatester",
    50: "juniormod",
    60: "mod",
    70: "dev",
    80: "admin",
    90: "creator"
}

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

def pretty_date(time=False):
    now = datetime.now()
    diff = now - time
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(second_diff / 60) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str(second_diff / 3600) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff / 7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff / 30) + " months ago"
    return str(day_diff / 365) + " years ago"