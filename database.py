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
    registered_date = DateTimeField(null=False)
    level = IntegerField(null=False, default=0)

    #Profile
    description = TextField(null=True)
    tag_line = CharField(null=True)
    gender = CharField(null=True)
    location = CharField(null=True)
    youtube = CharField(null=True)
    twitch = CharField(null=True)
    twitter = CharField(null=True)
    skype = CharField(null=True)

    def checkPassword(self, pw):
        return bcrypt.hashpw(pw, self.password) == self.password

User.create_table(True)

class Forum(BaseModel):
    title = CharField()
    desc = TextField()
    perm_view = IntegerField()
    perm_post = IntegerField()

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
    thread = IntegerField()
    response = ForeignKeyField('self', "responses")
    original = BooleanField()
    date = DateTimeField()
    content = TextField()

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

if __name__ == '__main__':
    u = User(username="b1naryth1ef", email="b1naryth1ef@gmail.com", password=hashPassword("b1n"), registered=True, registered_date=datetime.now(), level=100)
    u.save()
