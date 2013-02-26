from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from database import *
from datetime import datetime

forum = Blueprint('forum', __name__)

@forum.route('/')
@forum.route('/<page>')
def routeIndex(page=1):
    if not g.user: level = 0
    else: level = g.user.level
    cats = Forum.select().where((Forum.perm_view <= level) & (Forum.cat == True)).order_by(Forum.order)
    posts = ForumPost.select().where((ForumPost.first == True)).order_by(ForumPost.last_update.desc()).paginate(int(page), 20)
    return render_template("forum.html", cats=cats, posts=posts, cur=-1)

@forum.route('/b/<bid>')
@forum.route('/b/<bid>:<page>')
def routeBoard(bid=None, page=1):
    if not g.user: level = 0
    else: level = g.user.level
    if not bid: return flashy("No such board!", "error", "/forum")
    cats = Forum.select().where((Forum.perm_view <= level) & (Forum.cat == True)).order_by(Forum.order)
    board = Forum.select().where((Forum.perm_view <= level) & (Forum.cat == False) & (Forum.id == int(bid)))
    if not board.count(): return flashy("Invalid board!", "error", "/forum")
    sticks = ForumPost.select().where((ForumPost.forum == board), (ForumPost.first == True), (ForumPost.sticky==True)).order_by(ForumPost.last_update.desc()).paginate(int(page), 25)
    posts = ForumPost.select().where((ForumPost.forum == board), (ForumPost.first == True), (ForumPost.sticky==False)).order_by(ForumPost.last_update.desc()).paginate(int(page), 25)
    return render_template("forum.html", cats=cats, posts=[i for i in sticks]+[i for i in posts], board=board[0])

@forum.route('/b/<bid>/<pid>')
@forum.route('/b/<bid>/<pid>:<page>')
def routePost(bid=None, pid=None, page=1):
    if not g.user: level = 0
    else: level = g.user.level
    if not pid or not bid:
        return flashy("Invalid request!", "error", "/forum")
    p = ForumPost.select().where(ForumPost.id == int(pid))
    if not p.count():
        return flashy("No such post!", "error", "/forum")
    cats = Forum.select().where((Forum.perm_view <= level) & (Forum.cat == True)).order_by(Forum.order)
    return render_template("forum.html", post=p[0], cats=cats, page=int(page))

@forum.route('/addpost', methods=['POST'])
@reqLogin
def routeAddPost():
    if not request.form.get('title') or not request.form.get("content") or not request.form.get("board"):
        return flashy("Invalid add-post request!", "error", "/forum")
    b = Forum.select().where(Forum.id == int(request.form.get('board')))
    if not b.count(): return flashy("Invalid board!", "error", "/forum")
    b = b[0]
    if b.perm_post > g.user.level: return flashy("You dont have permission to do that!", "error", "/forum")
    if request.form.get('sticky') and g.user.level >= 60: stick = True
    else: stick = False
    p = ForumPost(
        author=g.user,
        forum=b,
        first=True,
        date=datetime.now(),
        content=request.form.get("content"),
        title=request.form.get("title"),
        sticky=stick)
    p.save()
    if 'thread' in request.form.keys(): pass
    return flashy("Added post!", "success", "/forum/b/%s/%s" % (b.id, p.id))

@forum.route('/replypost', methods=['POST'])
@reqLogin
def routeReplyPost():
    if not request.form.get("content") or not request.form.get("post"):
        return flashy("Invalid reply-post request!", "error", "/forum")
    p = ForumPost.select().where(ForumPost.id == int(request.form.get("post")))
    if not p.count(): return flashy("Invalid post!", "error", "/forum")
    p = p[0]
    if p.forum.perm_post > g.user.level: return flashy("You dont have permission to do that!", "error", "/forum")
    q = ForumPost.select().where(ForumPost.content == request.form.get("content"), ForumPost.author == g.user)
    if q.count(): return flashy("You've already posted that!", "error", "/forum")

    if p.locked: return flashy("That post is locked!", "error", "/forum")

    r = ForumPost(
        author=g.user,
        forum=p.forum,
        original=p,
        date=datetime.now(),
        content=request.form.get("content"),
        title=None)
    r.save()
    return flashy("Added reply!", "success", "/forum/b/%s/%s:%s" % (p.forum.id, p.id, r.getPage()))

@forum.route('/deletepost/<id>')
@reqLogin
def routeDeletePost(id=None):
    if not id: return flashy("Invalid delete request!", "error", "/forum")
    p = ForumPost.select().where(ForumPost.id == int(id))
    if not p.count(): return flashy("Invalid post!", "error", "/forum")
    p = p[0]
    if not p.author == g.user and not g.user.level >= 60:
        return flashy("You dont have permission to do that!", "error", "/forum")
    p.delete_instance()
    return flashy("Deleted post!", "success", "/forum")

@forum.route('/lockpost/<id>')
@reqLogin
def routeLockPost(id=None):
    if not id: return flashy("Invalid lock request!", "error", "/forum")
    if not g.user.level >= 60: return flashy("You dont have permission to do that!", "error", "/forum")
    p = ForumPost.select().where(ForumPost.id == int(id))
    if not p.count(): return flashy("Invalid post!", "error", "/forum")
    p = p[0]
    p.locked = True
    p.save()
    return flashy("Locked post!", "success", "/forum")
