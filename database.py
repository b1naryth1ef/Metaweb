from peewee import *
from datetime import *
import bcrypt

db = SqliteDatabase('database.db', threadlocals=True)

class BaseModel(Model):
    class Meta:
        database = db

def hashPassword(pw):
        return bcrypt.hashpw(pw, bcrypt.gensalt())

class User(BaseModel):
    username = CharField()
    email = CharField()
    password = CharField()
    registered = BooleanField(null=False)
    first_join = DateTimeField(null=True)
    last_join = DateTimeField(null=True)
    registered_date = DateTimeField(null=False)
    level = IntegerField(default=0)
    altlevel = IntegerField(default=0) #For visual purposes only (no lvl-checks)

    #Profile
    description = TextField(default="Nothing here yet!")
    tag_line = CharField(null=True)
    gender = CharField(default="ALL OF THE GENDERS")
    location = CharField(null=True)
    youtube = CharField(null=True)
    twitch = CharField(null=True)
    twitter = CharField(null=True)
    skype = CharField(null=True)

    def checkPassword(self, pw):
        return bcrypt.hashpw(pw, self.password) == self.password

    def getFriendship(self, other, getq=False, j=False):
        a = (Friendship.a == self) & (Friendship.b == other) & (Friendship.confirmed == True)
        b = (Friendship.a == other) & (Friendship.b == self) & (Friendship.confirmed == True)
        q = Friendship.select().where(a|b)
        if getq: return q
        elif j: return q.join(User)
        return q

    def getForumPosts(self):
        return ForumPost().select().where(ForumPost.author == self)

    def getFriends(self):
        res = []
        for i in self.getFriendships(j=True):
            if i.a == self: res.append(i.b)
            else: res.append(i.a)
        return res

    def getFriendships(self, j=False):
        q = Friendship().select().where((Friendship.a == self) | (Friendship.b == self), Friendship.confirmed == True)
        if j: q = q.join(User)
        return q

    def getFriendsAdded(self, j=False):
        q = Friendship.select().where(Friendship.a == self, Friendship.confirmed == True)
        if j: q = q.join(User)
        return q

    def isFriendsWith(self, other):
        return bool(self.getFriendship(other, getq=True).count())

    def canFriend(self, other):
        a = (Friendship.a == self) & (Friendship.b == other)
        b = (Friendship.a == other) & (Friendship.b == self)
        return not bool(Friendship.select().where(a|b).count())

    def getNotes(self):
        return Notification.select().where(Notification.user == self, Notification.read == False)

    def getAllNotes(self, date=False, sort=False):
        q = Notification.select().where(Notification.user == self)
        if date:
            return q.order_by(Notification.date.desc())
        return q

    def getNoteCount(self):
        return self.getNotes().count()

    def getGroupBadge(self, id):
        if id <= 20:
            return '<span class="label">Regular</span>'
        elif id == 30:
            return '<span class="label label-success">Donator</span>'
        elif id == 40:
            return '<span class="label label-info">Community Contributor</span>'
        elif id == 41:
            return '<span class="label label-info">Map Developer</span>'
        elif id == 42:
            return '<span class="label label-info">Beta Tester</span>'
        elif id == 50:
            return '<span class="label label-warning">Junior Moderator</span>'
        elif id == 51:
            return '<span class="label label-warning">Junior Developer</span>'
        elif id == 60:
            return '<span class="label label-warning">Moderator</span>'
        elif id == 61:
            return '<span class="label gay" style="background-color: #FF00FF;">Fgt</span>'
        elif id == 70:
            return '<span class="label label-important">Developer</span>'
        elif id == 80:
            return '<span class="label label-important">Admin</span>'
        elif id >= 90:
            return '<span class="label label-inverse">Creator</span>'

User.create_table(True)

class Notification(BaseModel):
    user = ForeignKeyField(User, "notes")
    read = BooleanField(default=False)
    title = CharField()
    content = TextField()
    ntype = CharField(default="success")
    reference = IntegerField(null=True)
    date = DateTimeField(default=datetime.now)

Notification.create_table(True)

class Forum(BaseModel):
    title = CharField()
    desc = TextField(null=True)
    perm_view = IntegerField()
    perm_post = IntegerField()
    order = IntegerField(null=True)
    cat = BooleanField(default=False)
    frontpage = BooleanField(default=False)
    parent = ForeignKeyField("self", "children")

    def getForums(self):
        q = Forum.select().where(Forum.parent == self)
        return q

    def getLatestPosts(self, limit):
        return ForumPost.select().where(ForumPost.forum == self, ForumPost.first == True).order_by(ForumPost.date.desc()).limit(limit)

Forum.create_table(True)

class BlogPost(BaseModel):
    author = ForeignKeyField(User, "blogs")
    forum_post = ForeignKeyField(Forum, "blogpost")
    date = DateTimeField()
    text = TextField()
    title = CharField()

BlogPost.create_table(True)

class ForumPost(BaseModel):
    author = ForeignKeyField(User, "posts")
    forum = ForeignKeyField(Forum, "threads")
    original = ForeignKeyField('self', "responses")
    first = BooleanField(default=False)
    #original = BooleanField()
    date = DateTimeField()
    content = TextField()
    title = CharField(null=True)
    views = IntegerField(default=0)

    #OP Stuff
    sticky = BooleanField(default=False)
    locked = BooleanField(default=False)
    last_update = DateTimeField(default=datetime.now)

    def isLocked(self):
        if self.original:
            return self.original.locked
        return self.locked

    def getUrl(self):
        if self.original: id = self.original.id
        else: id = self.id
        return "/forum/b/%s/%s:%s#%s" % (self.forum.id, id, self.getPage(), self.id)

    def getPage(self): #@DEV inefficient
        if not self.original: return 1
        q = [i for i in ForumPost.select().where(ForumPost.original == self.original).order_by(ForumPost.date)]
        if q.index(self)/10 == 0: return 1
        else: return (q.index(self)/10)+1

    def getLatestPost(self):
        q = self.getReplys(rev=True)
        if q.count():
            return q[0]
        else:
            return self

    def getNumberPosts(self):
        return ForumPost.select().where(ForumPost.original == self).count()

    def getReplys(self, rev=False):
        q = ForumPost.select().where((ForumPost.original == self)|(ForumPost.id == self.id))
        if rev: return q.order_by(ForumPost.date.desc())
        return q.order_by(ForumPost.date)

    def getThread(self, page=1):
        if page == 1: q = ForumPost.select().where((ForumPost.original == self)|(ForumPost.id == self.id))
        else: q = ForumPost.select().where((ForumPost.original == self))
        return q.order_by(ForumPost.date).paginate(page, 10)


ForumPost.create_table(True)

class Page(BaseModel):
    title = CharField()
    content = TextField()
    icon = CharField(default="icon-folder-open")
    perm_view = IntegerField(default=0)

Page.create_table(True)

class Friendship(BaseModel):
    a = ForeignKeyField(User, "friends")
    b = ForeignKeyField(User, "friends")
    confirmed = BooleanField()
    ignored = BooleanField()
    date = DateTimeField()
    note = ForeignKeyField(Notification)
    respdate = DateTimeField(null=True)

    def getNot(self, other):
        return self.a if self.a != other else self.b

Friendship.create_table(True)

class Donation(BaseModel):
    user = ForeignKeyField(User, "donations")
    stripeid = CharField()
    customerid = CharField()
    amount = DoubleField()
    active = BooleanField()
    created = DateTimeField(null=True)

Donation.create_table(True)

def setupForums():
    cat1 = Forum(title="MetaCraft", perm_view=0, perm_post=60, order=0, cat=True)
    cat2 = Forum(title="Main Discussion", perm_view=0, perm_post=60, order=1, cat=True)
    cat3 = Forum(title="Beta Discussion", perm_view=0, perm_post=60, order=2, cat=True)
    cat1.save()
    cat2.save()
    cat3.save()

    Forum(title="News", perm_view=0, perm_post=60, order=0, parent=cat1, cat=False, frontpage=True).save()
    Forum(title="Tech Blog", perm_view=0, perm_post=60, order=1, parent=cat1, cat=False).save()

    Forum(title="Main", perm_view=0, perm_post=0, order=0, parent=cat2, cat=False).save()
    Forum(title="Off-Topic", perm_view=0, perm_post=0, order=1, parent=cat2, cat=False).save()
    Forum(title="Media", perm_view=0, perm_post=0, order=2, parent=cat2, cat=False).save()

    Forum(title="Changelog", perm_view=0, perm_post=60, order=0, parent=cat3, cat=False).save()
    Forum(title="Bug Reports", perm_view=0, perm_post=60, order=0, parent=cat3, cat=False).save()

if __name__ == '__main__':
    u = User(username="b1naryth1ef", email="b1naryth1ef@gmail.com", password=hashPassword("b1n"), registered=True, registered_date=datetime.now(), level=90, last_join=datetime.now(), tag_line="Proh@x l33t c0d3r z0mg.", altlevel=70)
    u.save()
    u = User(username="testicle", email="test@test.com", password=hashPassword("test"), registered=True, registered_date=datetime.now(), level=30, last_join=datetime.now())
    u.save()
    setupForums()
