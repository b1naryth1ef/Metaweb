import sqlite3, os, sys, json, requests

conn = sqlite3.connect('database.db')

if not len(sys.argv) > 1:
    print "Please provide a migration file!"
    sys.exit(1)

if sys.argv[1] == "getdump":
    c = conn.cursor()
    for line in conn.iterdump():
        if not line.startswith("CREATE TABLE"): continue
        print line
    sys.exit(0)

if not os.path.exists(sys.argv[1]) and not sys.argv[1].startswith('http'):
    print "Migration file does not exist!"
    sys.exit(1)

if sys.argv[1].startswith('http'):
    cfg = requests.get(sys.argv[1]).json()
else:
    with open(sys.argv[1], "r") as f:
        cfg = json.load(f)

print "Loaded migration file!"
print "  # of Migrations: %s" % len(cfg['actions'])
if raw_input("Please enter Y to continue, or any key to abort: ").lower() != 'y':
    print "User aborted!"
    sys.exit(1)

c = conn.cursor()
for i, action in enumerate(cfg['actions']):
    print "Applying migration #%s of %s" % (i+1, len(cfg['actions']))
    c.execute(action)
print 'Database migrated!'
conn.commit()
conn.close()
