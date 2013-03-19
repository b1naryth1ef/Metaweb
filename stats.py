from datetime import datetime
from dateutil.rrule import *
from dateutil.relativedelta import *
import redis, os

graph_keys = [
    "{key}.{now.year}",
    "{key}.{now.year}.{now.month}",
    "{key}.{now.year}.{now.month}.{now.day}",
    "{key}.{now.year}.{now.month}.{now.day}.{now.hour}",
    "{key}.{now.year}.{now.month}.{now.day}.{now.hour}.{now.minute}"
]

#Freq, Limit, graph_keys ref
format_key = {
    "week": (DAILY, 7, 2)
}

class Field(object):
    def __init__(self, name, user=False):
        self.name = name
        self.user = user

    def load(self, holder, red):
        self.red = red
        self.holder = holder
        if self.user: self.key = "meta.stats.plugin.%s.user.{user}.%s" % (self.holder.id, self.name)
        else: self.key = "meta.stats.plugin.%s.%s" % (self.holder.id, self.name)

    def incr(self, value, user=None): pass

class GraphField(Field):
    def incr(self, value, user=None):
        for i in graph_keys:
            k = i.format(key=self.key.format(user=user), now=datetime.now())
            self.red.incr(k, value)

    def getGraph(self, t="week", start=None, user=None):
        vals = []
        if not start: start = datetime.now()
        freq, limit, key = format_key[t]
        for dt in rrule(freq, count=limit, dtstart=start):
            k = graph_keys[key].format(key=self.key.format(user=user), now=dt)
            #print k, "B:", graph_keys[key]
            v = self.red.get(k)
            if not v: v = 0
            vals.append((dt, float(v)))
        return vals

class StaticField(Field):
    def incr(self, value, user=None):
        self.red.incr(self.key.format(user=user), value)

    def getStatic(self):
        return self.red.get(self.key)

#Mixes
class StaticGraphField(Field):
    def __init__(self, name, user=False):
        Field.__init__(self, name, user)
        self.graphf = GraphField(name+"_g", user)
        self.staticf = StaticField(name+"_s", user)

    def load(self, holder, red):
        self.graphf.load(holder, red)
        self.staticf.load(holder, red)

    def incr(self, value, user=None):
        self.graphf.incr(value, user)
        self.staticf.incr(value, user)

    def getWeekly(self, user=None):
        dt = datetime.now()+relativedelta(days=-6)
        return self.getGraph(t="week", start=dt, user=user)

    def getStatic(self):
        return self.staticf.getStatic()

    def getGraph(self, *args, **kwargs):
        return self.graphf.getGraph(*args, **kwargs)

class PluginHolder(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.redis = redis.Redis("hydr0.com", password=os.getenv("REDISPASS"))
        self.fields = {}

    def getField(self, f):
        return self.fields[f]

    def addField(self, f):
        self.fields[f.name] = f
        f.load(self, self.redis)
        return f


plugins = {
    2: PluginHolder(2, "CTF")
}

plugins[2].addField(StaticGraphField("kills", user=True))
plugins[2].addField(StaticGraphField("deaths_pve", user=True))
plugins[2].addField(StaticGraphField("deaths_pvp", user=True))
