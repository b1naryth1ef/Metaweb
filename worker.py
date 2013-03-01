import os, redis, json, random, smtplib, string
from database import User, db

db.connect()
r = redis.Redis(host='mc.hydr0.com', password=os.getenv("REDISPASS"))

MESG = """
Hiya {username}!

This is an email letting you know we've recieved a registration request to join MetaCraft, from the minecraft account {username}!
If you have no clue what this is all about, you can just ignore this email and no action will be taken!

To create your MetaCraft profile: <a href="{url}">Click Here</a>

We'll be happy to see you on the website soon!

- MetaCraft Team
"""

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
    print opt, key
    sendEmail(opt, key)

def sendEmail(opt, key):
    SUBJECT = "MetaCraft registration for '%s'" % opt['username']
    FROM = "noreply@hydr0.com"
    text = MESG.format(url="http://m.hydr0.com/register?email=%s&id=%s" % (opt['email'], key), **opt)
    BODY = string.join((
            "From: %s" % FROM,
            "To: %s" % opt['email'],
            "Subject: %s" % SUBJECT,
            "",
            text
            ), "\r\n")
    server = smtplib.SMTP('localhost')
    server.sendmail(FROM, [opt['email']], BODY)
    server.quit()

while True:
    msg = r.blpop("meta.wqueue")
    try:
        msg = json.loads(msg[1])
    except:
        print "Error decoding json stuffs: %s" % str(msg[1])
        continue

    if msg['a'] == "check":
        val = User.get(User.email == msg['email'] | User.username == msg['username']) is not None
        msg = r.rpush("meta.squeue.%s" % msg['server'], json.dumps({'t': "resp", "id": msg['id'], "result": val}))
    elif msg['a'] == "reg":
        registerUser(msg)
