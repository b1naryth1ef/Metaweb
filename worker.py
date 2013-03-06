import os, redis, json, random, smtplib, string, thread, requests, time
from database import User, db
from ruser import RUser
from datetime import datetime
from util import group_key, pretty_date

db.connect()
r = redis.Redis("hydr0.com", password=os.getenv("REDISPASS"))

MESG = """
Hiya {username}!

This is an email letting you know we've recieved a registration request to join MetaCraft, from the minecraft account {username}!
If you have no clue what this is all about, you can just ignore this email and no action will be taken!

To create your MetaCraft profile: <a href="{url}">Click Here</a>

We'll be happy to see you on the website soon!

- MetaCraft Team
"""

need_reg_msgs = [
    "{C_RED}Hey! Looks like your not registered with us yet!",
    "{C_RED}->{C_GREEN} Unregistered users can't track stats, dispute infractions, or add friends!",
    "{C_RED}->{C_GREEN}  It's quick and easy to register! Type: /register myemail@blah.com"]

def sendEmail(opt, key):
    SUBJECT = "MetaCraft registration for '%s'" % opt['username']
    FROM = "noreply@hydr0.com"
    text = MESG.format(url="http://meta.hydr0.com/register?email=%s&id=%s" % (opt['email'], key), **opt)
    BODY = string.join(("From: %s" % FROM, "To: %s" % opt['email'], "Subject: %s" % SUBJECT, "", text), "\r\n")
    server = smtplib.SMTP('localhost')
    server.sendmail(FROM, [opt['email']], BODY)
    server.quit()

hooks = {}

def hook(name):
    def deco(f):
        def new(*args, **kwargs):
            thread.start_new_thread(f, args, kwargs)
        if not type(name) == list: nm = [name]
        else: nm = name
        for i in nm:
            hooks[i] = new
        return f
    return deco

def push(id, msg):
    r.rpush("meta.server.%s.queue" % id, json.dumps(msg))

@hook("reg")
def registerUser(opt):
    key = []
    for i in range(0, 16):
        key.append(random.choice("abcdefghijklmnopqrstuvwxyz123456789"))
    key = ''.join(key)
    val = json.dumps({
        "user": opt['username'],
        "key": key,
        "email": opt['email']
    })
    r.set("meta.register.%s" % opt['email'], val)
    print "REG:", opt, key
    #sendEmail(opt, key)

@hook("server_start")
def serverStart(obj):
    obj['data']['sid'] = obj['sid'] #@TODO fix
    r.hmset("meta.server.%s" % obj['sid'], obj['data'])
    r.delete("meta.server.%s.players" % obj['sid'])

@hook("server_stop")
def serverStop(obj):
    for i in r.smembers("meta.server.%s.players" % obj['sid']):
        handleUserQuit({'sid': obj['sid'], "u": i, })
    r.delete("meta.server.%s.players" % obj['sid'])

@hook('join')
def handleUserJoin(obj):
    if not obj['joined']: return
    u = RUser(obj['u'], 0, r)
    if u.isOnline() and not u.getCurrentServer()['sid'] == obj['sid']: #If the user is online, kick them from the first server
        push(obj['sid'], {"a": "kick", "u": obj['u'], "msg": "User joined another server..."})
    u.joinServer(obj['sid'])
    u.addServerHistory(obj['sid'])

    # Join Message
    q = User.select().where(User.username == obj['u'])
    if not q.count():
        packs = [{"a": "sendto", "user": obj['u'], "msg": i} for i in need_reg_msgs]
        push(obj['sid'], packs)
        return

    resp = [
        {"a": "sendto", "user": obj['u'], "msg": "{C_RED}{C_ITALIC}Your user level has been synced."},
        {"a": "user_level", "user": obj['u'], "level": q[0].level}]
    push(obj['sid'], resp)

    msg = [{"a": "sendto", "user": None, "msg": "{C_AQUA}%s {C_GOLD}{C_ITALIC}has joined %s" % (q[0].username, u.getCurrentServer()['name'])}]
    for fr in q[0].getFriends():
        tmp = RUser(fr.username, fr.id, r)
        if tmp.perma['CFG_NOTI_FRIEND_JOIN'] is False: continue
        if tmp.isOnline():
            msg[0]['user'] = tmp.name
            push(tmp.getCurrentServer()['sid'], msg)

@hook('quit')
def handleUserQuit(obj):
    u = RUser(obj['u'], 0, r)
    u.quitServer(obj['sid'])

    q = User.select().where(User.username == obj['u'])
    if not q.count(): return

    msg = [{"a": "sendto", "user": None, "msg": "{C_AQUA}%s {C_GOLD}{C_ITALIC}has left %s" % (q[0].username, u.getServerInfo(u.getLastServer()['sid'])['name'])}]
    for fr in q[0].getFriends():
        tmp = RUser(fr.username, fr.id, r)
        if tmp.perma['CFG_NOTI_FRIEND_QUIT'] is False: continue
        if tmp.isOnline():
            msg[0]['user'] = tmp.name
            push(tmp.getCurrentServer()['sid'], msg)

@hook('getattr')
def handleGetAttr(obj):
    u = RUser(obj['u'], 0, r)
    msgs = []
    if not u.exists():
        msgs.append({"a": "sendto", "user": obj['admin'], "msg": "{C_RED}{C_ITALIC}No such user!"})
        return push(obj['sid'], msgs)
    if obj['attr'] == "inf":
        msgs.append({"a": "sendto", "user": obj['admin'], "msg": "{C_RED}Infractions for {C_GRAY}'{C_AQUA}%s{C_GRAY}'" % u.name})
        for i, inf in enumerate(u.getInfractions()[:30]):
            post = ""
            if i > 30: break
            if inf['type'] == "ban":
                inf['type'] = "{C_RED}BAN"
            else:
                inf['type'] = "{C_YELLOW}TEMPBAN"
            if inf['type'] == "tban" and datetime.fromtimestamp(inf['expires']) < datetime.now():
                post = "{C_GOLD} -> {C_GRAY}[{C_LPURPLE}Expired{C_GRAY}]"
            elif inf['status'] == 2:
                post = "{C_GOLD} -> {C_GRAY}[{C_GREEN}Disputed{C_GRAY}]"
            m = "{C_AQUA}%s {C_GOLD}-{C_AQUA} %s {C_GOLD}-{C_AQUA} %s {C_GOLD}-{C_DAQUA}{C_ITALIC} %s {C_GOLD}- {C_GRAY}[{C_BLUE}%s{C_GRAY}]" % (i+1, inf['type'], inf['mod'], inf['msg'], pretty_date(datetime.fromtimestamp(inf['time'])))
            msgs.append({"a": "sendto", "user": obj['admin'], "msg": m+post})
        if len(msgs) == 1:
            msgs.append({"a": "sendto", "user": obj['admin'], "msg": "{C_RED}{C_ITALIC}  None!"})
    elif obj['attr'] == "act":
        msgs.append({"a": "sendto", "user": obj['admin'], "msg": "{C_RED}History for {C_GRAY}'{C_AQUA}%s{C_GRAY}'" % u.name})
        for i, h in enumerate(u.getHistory()[:30]):
            m = "{C_GREEN}%s: {C_AQUA}%s {C_GOLD}-> {C_RED}%s {C_GOLD}-> {C_DAQUA}%s {C_GRAY}[{C_BLUE}%s{C_GRAY}]" % (i+1, h['admin'], h['type'].title(), h['msg'], pretty_date(datetime.fromtimestamp(h['time'])))
            msgs.append({"a": "sendto", "user": obj['admin'], "msg": m})
        if len(msgs) == 1:
            msgs.append({"a": "sendto", "user": obj['admin'], "msg": "{C_RED}{C_ITALIC}  None!"})

    push(obj['sid'], msgs)

@hook('kick')
def handleUserKick(obj): pass

@hook('ban')
def handleUserBan(obj):
    u = RUser(obj['u'], 0, r)
    u.addInfraction("ban", obj['msg'], obj['admin'])

@hook('history')
def handleHistory(obj):
    u = RUser(obj['u'], 0, r)
    del obj['a']
    obj['time'] = time.time()
    u.addHistory(obj)

@hook('getinfo')
def handleGetInfo(obj):
    msgs = []
    u = RUser(obj['u'], 0, r)
    hq = u.getHistory([('type', "ban"), ('type', 'kick'), ('type', 'warn')])
    geo = requests.get("http://api.ipinfodb.com/v3/ip-city/", params={"key": "05f8b69eb84cd0ba1f2fc2fb74c43ff377a9ca3c5249c2e87226dcfb2309858f", "ip": obj['ip'], "format": "json"}).json
    msgs.append({"a": 'sendto', "user": obj['admin'], "msg": "{C_AQUA}  GeoIP: {C_RED}%s" % geo['countryName']})
    msgs.append({"a": 'sendto', "user": obj['admin'], "msg": "{C_AQUA}  Time Played: {C_RED}%s" % u.getTimePlayed(True)})
    msgs.append({"a": 'sendto', "user": obj['admin'], "msg": "{C_AQUA}  Infractions: {C_RED}%s" % u.getInfractionCount()})
    msgs.append({"a": 'sendto', "user": obj['admin'], "msg": "{C_AQUA}  Actions Against: {C_RED}%s" % len(hq)})
    msgs.append({'a': 'sendto', "user": obj['admin'], "msg": "{C_AQUA}  Notes: {C_RED}0"})
    push(obj['sid'], msgs)

while True:
    msg = r.blpop("meta.wqueue")
    try:
        m = json.loads(msg[1])
    except:
        print "Error decoding json stuffs: %s" % str(msg[1])
        continue

    for msg in m:
        if msg['a'] in hooks:
            print "Executing hook: %s" % msg['a']
            hooks[msg['a']](msg)
        else:
            print "Unknown hook: %s" % msg['a']
