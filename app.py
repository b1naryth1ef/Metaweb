from flask import Flask, render_template, Blueprint, g, flash, session
from flask.ext.gravatar import Gravatar
from database import *
import os, random, redis

#Views
from views.public import public
from views.admin import admin

app = Flask(__name__)
app.secret_key = "change_me"
rpw = os.getenv("REDISPASS")

app.register_blueprint(public)
app.register_blueprint(admin, url_prefix="/admin")
db.connect()

gravatar = Gravatar(
    app,
    size=100,
    rating='g',
    default='mm',
    force_lower=False
)

@app.before_request
def beforeRequest():
    g.redis = redis.Redis('mc.hydr0.com', password=rpw)
    g.db = db
    g.db.connect()
    if session.get('u'):
        g.user = User.select().where(User.username == session['u']).get()
    else:
        g.user = None

@app.after_request
def postRequest(r):
    g.db.close()
    return r

@app.route('/api/get_num_users')
def routeGetNumUsers():
    return random.randint(200, 300)

@app.template_filter('pretty')
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

if __name__ == '__main__':
    app.run(debug=True)
