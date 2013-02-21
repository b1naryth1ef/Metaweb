from peewee import *

db = SqliteDatabase('database.db')

class User(Model):
    username = CharField()
    email = CharField()
    password = CharField()
    registered = BooleanField()
    first_join = DateField()
    regsitered_date = DateField()

    #Profile
    description = CharField()
    tag_line = CharField()
    gender = CharField()
    location = CharField()
    youtube = CharField()
    twitch = CharField()
    twitter = CharField()
    skype = CharField()
