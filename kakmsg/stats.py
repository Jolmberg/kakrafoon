from marshmallow import Schema, fields
import marshmallow

class Song(object):
    def __init__(self, id=None, name=None, subtune=None, length=None, looplength=None, plays=None, playtime=None):
        self.id = id
        self.name = name
        self.subtune = subtune
        self.length = length
        self.looplength = looplength
        self.plays = plays
        self.playtime = playtime

class User(object):
    def __init__(self, id=None, name=None, plays=None, playtime=None):
        self.id = id
        self.name = name
        self.plays = plays
        self.playtime = playtime


class SongSchema(Schema):
    id = fields.Int()
    name = fields.Str(missing=None)
    subtune = fields.Int(missing=None)
    length = fields.Int(missing=None)
    looplength = fields.Int(missing=None)
    plays = fields.Int(missing=None)
    playtime = fields.Int(missing=None)

    @marshmallow.post_load
    def make_song(self, data):
        return Song(**data)

class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str(missing=None)
    plays = fields.Int(missing=None)
    playtime = fields.Int(missing=None)

    @marshmallow.post_load
    def make_User(self, data):
        return User(**data)

