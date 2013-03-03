import json

#Infractions status
#0 - Undisputed
#1 - Dispute filed, waiting admins
#2 - Dispute accepted
#3 - Dispute denied

class RUser(object):
    def __init__(self, name, id, red):
        self.id = id
        self.name = name.lower()
        self.red = red

        self.ukey = "meta.user.%s" % self.name

    def isBanned(self):
        return self.red.exists("%s.banned" % self.ukey)

    def getInfraction(self, id):
        q = self.red.lindex("%s.infractions" % self.ukey, id)
        if q:
            return json.loads(q)

    def getInfractionCount(self):
        return self.red.llen("%s.infractions" % self.ukey)

    def getInfractions(self, rev=False):
        vals = []
        for i, item in enumerate(self.red.lrange("%s.infractions" % self.ukey, 0, -1)):
            vals.append(json.loads(item))
            vals[-1]['id'] = i
        if rev: vals.reverse()
        return vals

    def getActiveInfractionCount(self, disputed=False, waiting=False, seen=False):
        num = 0
        for item in self.getInfractions():
            if item['status'] in [0, 1, 3]:
                if seen and item['seen']: continue
                if disputed and item['status'] == 1: continue
                if waiting and item['status'] != 1: continue
                num += 1
        return num

    def updateInfraction(self, id, val):
        print id, val
        self.red.lset("%s.infractions" % self.ukey, id, json.dumps(val))
