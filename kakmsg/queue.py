from marshmallow import Schema, fields
import marshmallow

class Song(object):
    def __init__(self, key=None, artist=None, song=None, filename=None,
                 url=None, length=None, bitrate=None, subtune=None, loops=None):
        self.key = key
        self.artist = artist
        self.song = song
        self.filename = filename
        self.url = url
        self.bitrate = bitrate
        self.length = length
        self.subtune = subtune
        self.loops = loops


class QueueItem(object):
    def __init__(self, user, key=None, songs=None):
        self.key = key
        self.user = user
        if songs is None:
            self.songs = []
        else:
            self.songs = songs


class Queue(object):
    def __init__(self, items=[]):
        self.items = items
        
        
class SongSchema(Schema):
    key = fields.Int()
    artist = fields.Str(missing=None)
    song = fields.Str(missing=None)
    filename = fields.Str(missing=None)
    url = fields.Str(missing=None)
    bitrate = fields.Int(missing=None)
    length = fields.Int(missing=None)
    subtune = fields.Int(missing=None)
    loops = fields.Int(missing=None)

    @marshmallow.post_load
    def make_song(self, data):
        return Song(**data)

    
class QueueItemSchema(Schema):
    key = fields.Int()
    user = fields.Str()
    songs = fields.Nested(SongSchema, many=True)

    @marshmallow.post_load
    def make_queueitem(self, data):
        return QueueItem(**data)

    
class QueueSchema(Schema):
    items = fields.Nested(QueueItemSchema, many=True)

    @marshmallow.post_load
    def make_queue(self, data):
        return Queue(**data)
