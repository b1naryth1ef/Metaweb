from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from datetime import datetime
from database import *
import json

public = Blueprint('public', __name__)

class UserStats():
    def __init__(self, user):
        self.u = user.lower()

    def getServer(self):
        return g.redis.get("meta.user.%s.online")

    def online(self):
        return g.redis.exists("meta.user.%s.online" % self.u)

    def kd(self, t="pvp"):
        return self.kills()/self.deaths()

    def kills(self, t="pvp"):
        return float(150) #g.redis.get("meta.stat.%s.%s.kills" % (t, self.u))

    def deaths(self, t="pvp"):
        return float(300) #g.redis.get('meta.stat.%s.%s.deaths' % (t, self.u))

    def kdchart(self, t):
        kills = float(self.kills(t))
        deaths = float(self.deaths(t))
        if kills > deaths:
            k = (kills/deaths)*10
            d = 100-k
        else:
            d = (deaths/kills)*10
            k = 100-d
        info = [
            {"label": "Kills", 'data':[[1, k]]},
            {"label": "Deaths", 'data':[[1, d]]}
        ]
        return json.dumps(info)

@public.route('/')
def routeIndex():
    posts = []
    forum = Forum.select().where(Forum.frontpage == True)
    if forum.count():
        posts = forum[0].getLatestPosts(5)
    return render_template('base.html', posts=posts)

@public.route('/logout/')
def routeLogout():
    if session.get('u'):
        session['u'] = None
        return flashy("You've have been logged out. See ya soon!", "success", "/")
    return redirect('/')

@public.route('/login/', methods=['POST'])
def routeLogin():
    if session.get('u'):
        return flashy("You are already logged in!", "warning", "/")
    if 'user' in request.values and 'pw' in request.values:
        u = User.select().where(User.username == request.values['user'])
        if u.count():
            u = u.get()
            if u.checkPassword(request.values['pw']):
                #q = Infractions.select().where((Infractions.user==u) & (Infractions.permban==True))
                #if q.count():
                #    return flashy("You are banned from the site!", "error", "/")
                session['u'] = u.username
                return flashy("Welcome back %s!" % u.username, "success", "/")
        return flashy("Invalid username/password!", "error", "/")
    else:
        return flashy("Invalid login request!", "error", "/")

# @public.route('/register/')
# def routeRegister():
#     if 'email' in request.values and 'id' in request.values:
#         key = 'meta.register.%s' % request.get('email')
#         if g.redis.exists(key):
#             val = json.loads(g.redis.get(key))
#             if val['key'] == request.get('id'):
#                 return render_template("register.html", email=request.values.get('email'), username=val['user'])
#     return flashy("Invalid register request!", "error", "/")

@public.route("/u/<user>")
def routeProfile(user=None):
    if not user:
        return flashy("You must specify a user!", "error", "/")
    u = User.select().where(User.username ** user)
    if u.count():
        return render_template("profile.html", user=u[0], ustat=UserStats(u[0].username))
    return flashy("No such user '%s'" % user, "error", "/")

@public.route("/p/<int:id>")
def routePage(id=None):
    p = Page().select().where(Page.id==id)
    if not p.count():
        return flashy("No such page!", "error", "/")
    return render_template("page.html", page=p[0])

@public.route("/register/", methods=["GET", "POST"])
def routeRegister():
    if g.user:
        return flashy("You cannot confirm an email when you are logged in!", "error", "/")
    if not request.values.get('email') or not request.values.get("id"):
        return flashy("Invalid register request!", "error", "/")

    if g.redis.exists("meta.register.%s" % request.values.get('email')):
        v = g.redis.get("meta.register.%s" % request.values.get("email"))
        try:
            v = json.loads(v)
        except:
            print "Error w/ conf: %s" % v
            return flashy("Error with confirmation request!", "error", "/")

        if v['key'] == request.values.get("id"):
            if not request.values.get("pw"):
                return render_template("register.html", id=request.values.get("id"), email=request.values.get("email"))
            u = User()
            u.username = v['user']
            u.email = v['email']
            u.password = request.values.get("pw")
            u.registered = True
            u.registered_date = datetime.now()
            u.level = 0
            u.altlevel = 0
            u.save()
            g.user = u
            session['u'] = u.username
            g.redis.delete("meta.register.%s" % u.email)
            return flashy("You are now registered! Enjoy!", "success", "/")
    return flashy("Invalid confirmation request!", "error", "/")
