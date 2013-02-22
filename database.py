from peewee import *
from datetime import *
import bcrypt

db = SqliteDatabase('database.db')

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

    def getFriends(self, j=False):
        q = Friendship().select().where(Friendship.a == self, Friendship.b == self, Friendship.confirmed == True)
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

    def getAllNotes(self, date=False):
        q = Notification.select().where(Notification.user == self)
        if date:
            return q.order_by(Notification.date)
        return q

    def getNoteCount(self):
        return self.getNotes().count()


User.create_table(True)

class Notification(BaseModel):
    user = ForeignKeyField(User, "notes")
    read = BooleanField(default=False)
    title = CharField()
    content = TextField()
    ntype = CharField(default="success")
    date = DateTimeField(default=datetime.now)

Notification.create_table(True)

class Forum(BaseModel):
    title = CharField()
    desc = TextField(null=True)
    perm_view = IntegerField()
    perm_post = IntegerField()
    order = IntegerField(null=True)
    cat = BooleanField(default=False)
    parent = ForeignKeyField("self", "children")

    def getForums(self):
        q = Forum.select().where(Forum.parent == self)
        return q

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
    order = IntegerField()
    #original = BooleanField()
    date = DateTimeField()
    content = TextField()
    title = CharField()
    views = IntegerField(default=0)

    #OP Stuff
    sticky = BooleanField(default=False)
    locked = BooleanField(default=False)
    update = DateTimeField(default=datetime.now)

    def getLatestPost(self):
        q = ForumPost.select().where(ForumPost.original == self).order_by(ForumPost.date)
        if q.count():
            return q[0]
        else:
            return self

    def getNumberPosts(self):
        return ForumPost.select().where(ForumPost.original == self).count()

ForumPost.create_table(True)

class Infractions(BaseModel):
    user = ForeignKeyField(User, "infractions")
    admin = ForeignKeyField(User, "penalties")
    desc = TextField()
    start_date = DateTimeField()
    end_date = DateTimeField()

    permban = BooleanField()
    kick = BooleanField()

Infractions.create_table(True)

class Friendship(BaseModel):
    a = ForeignKeyField(User, "friends")
    b = ForeignKeyField(User, "friends")
    confirmed = BooleanField()
    ignored = BooleanField()
    date = DateTimeField()
    respdate = DateTimeField(null=True)

Friendship.create_table(True)

if __name__ == '__main__':
    u = User(username="b1naryth1ef", email="b1naryth1ef@gmail.com", password=hashPassword("b1n"), registered=True, registered_date=datetime.now(), level=90, last_join=datetime.now(), tag_line="Proh@x l33t c0d3r z0mg.")
    u.save()
    u = User(username="testicle", email="test@test.com", password=hashPassword("test"), registered=True, registered_date=datetime.now(), level=30, last_join=datetime.now())
    u.save()
    f1 = Forum(title="General", perm_view=0, perm_post=0, order=0, cat=True)
    f1.save()
    f = Forum(title="News", perm_view=0, perm_post=60, parent=f1, cat=False)
    f.save()
    f = Forum(title="Open Discussion", perm_view=0, perm_post=0, parent=f1, cat=False)

    f2 = Forum(title="Beta", perm_view=0, perm_post=0, order=1, cat=True)
    f2.save()
    f = Forum(title="Bug Reports", perm_view=0, perm_post=0, parent=f2, cat=False)
    f.save()
