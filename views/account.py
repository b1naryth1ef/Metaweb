from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from datetime import datetime
from database import *

acct = Blueprint('account', __name__)

friend_msg = """
It looks like {user} wants to be your friend! If you <b>dont</b> want to be {user}'s friend, they will not be notified of your choice. <br />
<a href="/acct/friend/{user}/conf" class="btn btn-success btn-mini">Confirm!</a>
<a href="/acct/friend/{user}/deny" class="btn btn-danger btn-mini">Deny!</a>
"""

@acct.route("/")
@reqLogin
def routeIndex():
    return render_template("account.html")

@acct.route("/friend/<user>/<action>")
@reqLogin
def routeFriends(user=None, action=None):
    if not user or not action:
        return "Invalid Request", 400
    q = User.select().where(User.username==user)
    if q.count(): user = q[0]
    else: return flashy("That user doesnt seem to exist!", "error", "/")

    if g.user == user:
        return flashy("LOLNOPE", "error", "/")

    if action == "add":
        if not g.user.canFriend(user):
            return flashy("You can't friend that user!", "error", "/")
        f = Friendship(a=g.user, b=user, confirmed=False, ignored=False, date=datetime.now())
        n = Notification(user=user, title="%s wants to be your friend!" % g.user.username, content=friend_msg.format(user=g.user.username))
        f.save()
        n.save()
        return flashy("Your friend request has been sent too '%s'!" % user.username, "success", "/")
    elif action == "rmv":
        if not g.user.isFriendsWith(user):
            return flashy("Your not friends with that user!", "error", "/")
        f = g.user.getFriendship(user)
        f[0].delete_instance()
        return flashy("You are no longer friends with '%s' :(" % user.username, "success", "/")
    elif action == "conf":
        f = Friendship.select().where(Friendship.a == user, Friendship.b == g.user, Friendship.confirmed == False, Friendship.ignored == False)
        if not f.count():
            return flashy("Invalid link!", "error", "/")
        f = f[0]
        f.confirmed = True
        f.respdate = datetime.now()
        f.save()
        return flashy("You are now friends with %s" % user.username, "success", "/acct")
    elif action == "deny":
        f = Friendship.select().where(Friendship.a == user, Friendship.b == g.user, Friendship.confirmed == False, Friendship.ignored == False)
        if not f.count():
            return flashy("You've already responded to this request!", "error", "/")
        f = f[0]
        f.ignored = True
        f.respdate = datetime.now()
        f.save()
        return flashy("The friend request from %s has been denied!" % user.username, "warning", "/acct")


@acct.route('/note/<id>/<action>')
@reqLogin
def routeNotes(id=None, action=None):
    if not id or not id.isdigit() or not action:
        return "Invalid Request", 400

    q = Notification.select().where(Notification.id == int(id))
    if q.count(): note = q[0]
    else:
        return flashy("That note does not exist!", "error", "/acct")

    if action == "markread":
        note.read = True
        note.save()
        return "success"

@acct.route('/edit', methods=['POST'])
@reqLogin
def routeEdit():
    fields = ["tag_line", "gender", "location", "youtube", "twitch", "twitter", "skype", "description"]

    for k, v in request.form.items():
        if k in fields:
            setattr(g.user, k, v)
    g.user.save()

    return flashy("Edited profile!", "success", "/acct")