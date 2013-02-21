from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from database import *
import json

public = Blueprint('public', __name__)

@public.route('/')
def routeIndex():
    posts = BlogPost.select().order_by(BlogPost.date).join(User).limit(5)
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
                session['u'] = u.username
                return flashy("Welcome back %s!" % u.username, "success", "/")
        return flashy("Invalid username/password!", "error", "/")
    else:
        return flashy("Invalid login request!", "error", "/")

@public.route('/register/')
def routeRegister():
    if 'email' in request.values and 'id' in request.values:
        key = 'meta.register.%s' % request.get('email')
        if g.redis.exists(key):
            val = json.loads(g.redis.get(key))
            if val['key'] == request.get('id'):
                return render_template("register.html", email=request.values.get('email'), username=val['user'])
    return flashy("Invalid register request!", "error", "/")

@public.route('/blog/p/<i>')
@public.route('/blog/')
@public.route('/blog/<page>')
def routeBlog(i=None, page=1):
    if i and i.isdigit():
        posts = BlogPost.select().where(BlogPost.id == int(i)).join(User)
        if posts.count():
            return render_template('blog.html', post=posts[0])
        else:
            return flashy("Invalid post ID!", "error", "/blog/")
    #if not isinstance(page, int) or page.isdigit(): return flashy("Invalid page!", "error", "/blog/")
    posts = BlogPost.select().paginate(int(page), 10).order_by(BlogPost.date).join(User)
    return render_template('blog.html', posts=posts)
