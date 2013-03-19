from flask import Blueprint, render_template, flash, redirect, request, g, session
from util import reqLogin, reqLevel, flashy
from ruser import RUser
from datetime import datetime
from database import *
from stats import plugins
import time, json

graph = Blueprint('graph', __name__)
dthandler = lambda obj: time.mktime(obj.timetuple()) if isinstance(obj, datetime) else None

@graph.route("/poc/<user>")
def graphPoc(user=None):
    u = User.select().where(User.username ** user)
    if not u.count(): return flashy("Unknown user!", "error", "/")
    u = u[0]
    ru = RUser(u.username, u.id, g.redis)
    graph1 = {"key": "Kills", "values": plugins[2].getField("kills").getWeekly(user=u.username)}
    graph2 = {"key": "Deaths (PvE)", "values": plugins[2].getField("deaths_pve").getWeekly(user=u.username)}
    graph3 = {"key": "Deaths (PvP)", "values": plugins[2].getField("deaths_pvp").getWeekly(user=u.username)}
    end = json.dumps([graph1, graph2, graph3], default=dthandler)
    return render_template("graph_poc.html", u=u, ru=ru, plugins=plugins, v=end)
