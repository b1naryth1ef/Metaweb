import json, time, random

#Infractions status
#0 - Undisputed
#1 - Dispute filed, waiting admins
#2 - Dispute accepted
#3 - Dispute denied

#Infractions:
# status: int
# expires: float/null
# msg: string
# time: float
# mod: string
# type: string
# id: int
# dispute: string
# key: string

super_iter = [("minute", 60), ("hour", 24), ("day", 7), ("week", None), (None, None)]

class PermaStore(object):
    def __init__(self, ukey, red):
        self.ukey = ukey
        self.red = red

    def __getitem__(self, i):
        return self.red.hget("%s.permastore" % self.ukey, i)

    def __setitem__(self, i, v):
        return self.red.hset("%s.permastore" % self.ukey, i, v)


class RUser(object):
    def __init__(self, name, id, red):
        self.id = id
        self.name = name.lower()
        self.red = red
        self.ukey = "meta.user.%s" % self.name
        self.perma = PermaStore(self.ukey, self.red)

    def exists(self):
        return self.red.exists(self.ukey)

    def getTimePlayed(self, nice=False):
        v = self.red.get("%s.playtime" % self.ukey)
        if not v: return
        v = float(v)
        if not nice: return v
        for index, i in enumerate(super_iter):
            if v > i[1] and super_iter[index+1] is not None: v = v/i[1]
            else:
                if int(v) > 1: m = i[0]+'s'
                else: m = i[0]
                return "about %s %s" % (int(v), m)

    def getServerInfo(self, id):
        return self.red.hgetall("meta.server.%s" % id)

    def getCurrentServer(self):
        id = self.red.get("%s.server" % self.ukey)
        if not id: return None
        return self.getServerInfo(id)

    def getLastServer(self):
        if not self.red.llen("%s.play_history" % self.ukey): return None
        return json.loads(self.red.lrange("%s.play_history" % self.ukey, 0, 0)[0])

    def isOnline(self):
        return self.red.exists("%s.server" % self.ukey)

    def isBanned(self):
        return self.red.exists("%s.banned" % self.ukey)

    def addServerHistory(self, sid):
        if self.red.llen("%s.play_history" % self.ukey) >= 10:
            self.red.rpop("%s.play_history" % self.ukey)
        m = {"sid": sid, "stime": time.time(), "etime": 0}
        self.red.lpush("%s.play_history" % self.ukey, json.dumps(m))

    def joinServer(self, sid):
        self.red.set(self.ukey, 1)
        self.red.sadd("meta.server.%s.players" % sid, self.name)
        self.red.set("%s.server" % self.ukey, sid)

    def quitServer(self, sid):
        # Set the endtime
        if self.isOnline():
            i = json.loads(self.red.lrange("%s.play_history" % self.ukey, 0, 0)[0])
            i['etime'] = time.time()
            self.red.lset("%s.play_history" % self.ukey, 0, json.dumps(i))
            self.red.incr("%s.playtime" % self.ukey, int((i['etime']-i['stime'])/60))
        self.red.srem("meta.server.%s.players" % sid, self.name)
        self.red.delete("%s.server" % self.ukey)

    def addHistory(self, obj):
        self.red.lpush("%s.history" % self.ukey, json.dumps(obj))

    def getHistory(self, match=[], strict=False, rev=False):
        res = []
        for item in self.red.lrange("%s.history" % self.ukey, 0, -1):
            item = json.loads(item)
            if len(match):
                for i in match:
                    if item[i[0]] == i[1]:
                        res.append(item)
                    elif strict: break
            else: res.append(item)
        if rev:
            res.reverse()
        return res

    def getLastPost(self):
        if self.red.exists("%s.last_post" % self.ukey):
            return float(self.red.get("%s.last_post" % self.ukey))
        else: return 0

    def setLastPost(self):
        self.red.set("%s.last_post" % self.ukey, time.time())

    def addInfraction(self, typ, msg, admin, key=None):
        if key: key = random.randint(11111, 99999)
        inf = {
            'id': self.red.incr("meta.infractions"),
            'type': typ,
            "msg": msg,
            'mod': admin,
            "status": 0,
            "time": time.time(),
            "expires": None,
            "key": key}
        self.red.lpush("%s.infractions", inf['id'])
        self.red.hmset("meta.infractions.%s" % inf['id'], inf)

    def getInfraction(self, id):
        return self.red.hgetall("meta.infraction.%s" % id)

    def getInfractionCount(self):
        return self.red.llen("%s.infractions" % self.ukey)

    def getInfractions(self, rev=False):
        vals = []
        for id in self.red.lrange("%s.infractions" % self.ukey, 0, -1):
            vals.append(self.red.hgetall("meta.infraction.%s" % id))
        if rev: vals.reverse()
        return vals

    def getActiveInfractionCount(self, disputed=False, waiting=False, seen=False):
        num = 0
        for item in self.getInfractions():
            if item['status'] in [0, 1, 3]:
                if seen and self.red.sismember("%s.infractions_seen" % item['id']): continue
                if disputed and item['status'] == 1: continue
                if waiting and item['status'] != 1: continue
                num += 1
        return num

    def updateInfraction(self, id, val):
        self.red.hmset("meta.infractions.%s" % val['id'], val)
