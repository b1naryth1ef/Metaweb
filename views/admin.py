from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from database import *
from datetime import datetime
import json, markdown

admin = Blueprint('admin', __name__)

def getStats():
    data = {}
    data['num_users'] = User.select().count()
    return data

@admin.route('/')
@reqLevel(60)
def routeIndex():
    return render_template("admin.html", stats=getStats())


@admin.route('/delete_blog_post')
@reqLevel(60)
def routeEdit(id):
    post = BlogPost.select.where(BlogPost.id == int(id))
    if post.count():
        post[0].delete()
        return flashy("Post deleted!", "success", "/admin/")
    return flashy("Unknown post! Delete failed!", "error", "/admin/")

@admin.route('/edit/<id>')
@admin.route('/delete/<id>')
@reqLevel(60)
def routeEdit(id):
    post = BlogPost.select().where(BlogPost.id == int(id)).join(User)
    if post.count(): post = post[0]
    else: return flashy("Unknown post ID!", "error", "/admin/")
    return render_template("admin.html", post=post)

@admin.route('/update_blog_post', methods=["POST"])
@reqLevel(60)
def routeUpdateBlogPost():
    post = BlogPost().select().where(BlogPost.id == int(request.values.get('id', -1)))
    if post.count():
        post = post[0]
        post.title = request.values.get('title', post.title)
        if request.values.get("content"):
            post.text = markdown.markdown(request.values.get('content'))
        post.save()
        return flashy("Blog post <a href='/blog/p/%s'>%s</a> edited!" % (post.id, post.id), "success", "/admin/")
    return flashy("Error editing blog post!", "error", "/admin/")


@admin.route('/create_blog_post', methods=["POST"])
@reqLevel(60)
def routeCreateBlogPost():
    if "title" in request.values.keys() and "content" in request.values.keys():
        text = markdown.markdown(request.values.get('content'))
        post = BlogPost(author=g.user, date=datetime.now(), title=request.values.get('title'), text=text)
        post.save()
        return flashy("Blog post <a href='/blog/p/%s'>%s</a> created!" % (post.id, post.id), "success", "/admin/")
    return flashy("Error creating blog post!", "error", "/admin/")
