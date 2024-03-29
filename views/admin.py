from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from database import *
from datetime import datetime
from ruser import RUser
import json, markdown, os

admin = Blueprint('admin', __name__)

def getStats():
    data = {}
    data['num_users'] = User.select().count()
    return data

@admin.route('/u/<int:user>')
@reqLevel(60)
def routeUser(user=None):
    u = User.select().where(User.id == user)
    if not u.count():
        return flashy("That user does not exist!", "error", "/admin/")
    return render_template("admin.html", user=u[0], ruser=RUser(u[0].username, u[0].id, g.redis))

@admin.route('/u/warn_user', methods=['POST']) #This is special: jquery API stuff
@reqLevel(60)
def routeWarnUser():
    if not request.form.get("user") or not request.form.get("msg"):
        flash("Invalid form content!", "error")
        return "err:0"
    q = User.select().where(User.id == int(request.form.get('user')))
    if not q.count():
        flash("Invalid user id!", "error")
        return "err:1"
    n = Notification(
        user=q[0],
        title="Administrator Warning!",
        content=request.form.get("msg"),
        ntype="error")
    n.save()
    flash("Warned the user!", "success")
    return "success"

@admin.route('/u/set_group', methods=['POST']) #also special
@reqLevel(60)
def routeSetGroup():
    if not request.form.get("group") or not request.form.get("user") or not request.form.get("altgroup"):
        print request.form
        flash("Invalid form content!", 'error')
        return "err:0"
    q = User.select().where(User.id == int(request.form.get('user')))
    if not q.count():
        flash("Invalid user id!", "error")
        return "err:1"
    if int(request.form.get("group")) > g.user.level:
        flash("You cant give a user group-access higher than your own!", "error")
        return "err:2"
    u = q[0]
    u.level = int(request.form.get("group"))
    u.altlevel = int(request.form.get("altgroup"))
    u.save()
    flash("Set the users group!", "success")
    return "success"

@admin.route('/')
@admin.route('/<page>')
@reqLevel(60)
def routeIndex(page=1):
    users = User.select().paginate(page, 50)
    if g.missed and g.user.level >= 70:
        s = ("are", "s") if g.missed > 1 else ("is", "")
        flash("There %s %s git-commit%s waiting to be deployed!" % (s[0], g.missed, s[1]), "warning")
    return render_template("admin.html", stats=getStats(), users=users, page=page, RUser=RUser)

@admin.route('/edit/<id>')
@admin.route('/delete/<id>')
@reqLevel(60)
def routeEdit(id):
    post = BlogPost.select().where(BlogPost.id == int(id)).join(User)
    if post.count(): post = post[0]
    else: return flashy("Unknown post ID!", "error", "/admin/")
    return render_template("admin.html", post=post)

@admin.route('/page/create', methods=['POST'])
@reqLevel(60)
def routeCreatePage():
    if not request.form.get("title") or not request.form.get("content"):
        return flashy("Invalid page-creation request!", "error", "/admin/")

    p = Page(
        title=request.form.get("title"),
        content=request.form.get("content"),
        icon=request.form.get("icon", "icon-folder-open"))
    p.save()

    return flashy("Page created!", "success", "/admin")

@admin.route('/page/edit', methods=['POST'])
@reqLevel(60)
def routeEditPage(): pass

@admin.route('/page/delete/<id>')
@reqLevel(60)
def routeDeletPage(id=None): pass

@admin.route("/infraction/<int:uid>/<int:id>")
@admin.route("/infraction/<int:uid>/<int:id>/<action>")
@reqLevel(60)
def routeViewInfraction(uid, id, action=None):
    u = User.select().where(User.id == int(uid))
    if not u.count(): return flashy("Invalid user id!", "error", "/admin")
    o = RUser(u[0].username, u[0].id, g.redis)
    if id >= o.getInfractionCount(): return flashy("Invalid infraction ID!", "error", "/admin")
    inf = o.getInfraction(id)
    inf['id'] = id

    if not action: return render_template("infraction.html", inf=inf, infu=u[0])
    if action == "deny": inf['status'] = 3
    elif action == "accept": inf['status'] = 2
    o.updateInfraction(id, inf)
    return flashy("Infraction updated!", "success", "/admin/")

@admin.route("/redeploy/")
def routeRedeploy():
    f = os.popen('ps aux | grep "gunicorn: master \[app\:app\]"').readlines()
    if not len(f) == 1:
        return flashy("Could not find master-PID", "error", "/admin/")
    line = [i for i in f[0].strip().split(' ') if i != '']
    if not len(line) == 13:
        return flashy("Could not decipher ps line!", "error", "/admin/")
    pid = line[1]
    os.popen("git pull origin master")
    flash("Redeployed", "success")
    os.popen("kill -HUP %s" % pid)
    return redirect("/admin")
