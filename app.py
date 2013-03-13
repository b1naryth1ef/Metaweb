from flask import Flask, g, session, request
from flask.ext.gravatar import Gravatar
from datetime import datetime
#from raven.contrib.flask import Sentry
from database import *
from git import *
from ruser import RUser
import os, redis, json

#Views
from views.public import public
from views.admin import admin
from views.account import acct
from views.forum import forum

app = Flask(__name__)
app.secret_key = "change_me"
app.config['SENTRY_DSN'] = "http://25a16ac496ac42ee864d8611fbe3a730:d2673a44f27c42cdb75d4ff646d08ebe@debug.hydr0.com/2" #@TODO change before release
rpw = os.getenv("REDISPASS")
GIT_REV = os.popen("git log -n 1").readline().split(' ', 1)[-1][:12]

app.register_blueprint(public)
app.register_blueprint(admin, url_prefix="/admin")
app.register_blueprint(acct, url_prefix="/acct")
app.register_blueprint(forum, url_prefix="/forum")
#sentry = Sentry(app)
db.connect()

#Load Commits
missed_coms = 0
changes = []
repo = Repo(".")
for i in repo.iter_commits("master", max_count=5):
    changes.append(i)

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
    g.gitrev = GIT_REV
    g.changes = changes
    if session.get('u'):
        g.user = User.select().where(User.username == session['u']).get()
        g.ruser = RUser(g.user.username, g.user.id, g.redis)
        g.missed = missed_coms
    else:
        g.user = None

@app.after_request
def postRequest(r):
    g.db.close()
    return r

@app.route('/api/githook', methods=["POST"])
def routeGitHook():
    global missed_coms
    if not request.remote_addr == "63.246.22.222":
        return "Invalid IP :3"
    for com in request.json['commits']:
        if com['branch'] == "master": missed_coms[0] += 1


@app.route('/api/get_num_users')
def routeGetNumUsers():
    return json.dumps({'data': g.redis.get('meta.online')})

@app.template_filter('pages')
def pages(i):
    return range(1, int(i)+2)

@app.template_filter('plural')
def pluralize(a, b):
    if b == 1:
        return a
    else:
        return a+"s"

@app.template_filter("expired")
def expired(i):
    if datetime.now() > i: return True
    return False

@app.template_filter("rawtime")
def raw_time(i):
    obj = datetime.fromtimestamp(int(i))
    return obj

@app.template_filter("rawdate")
def raw_date(i):
    obj = datetime.fromtimestamp(int(i))
    return pretty_date(obj)

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
