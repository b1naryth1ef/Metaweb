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
def routeEditPage(): pass

@admin.route('/page/delete/<id>')
def routeDeletPage(id=None): pass