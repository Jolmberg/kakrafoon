from marshmallow import Schema, fields
import marshmallow

class Song(object):
    def __init__(self, filename=None, url=None, subtune=None, loops=None, fileid=None):
        if filename is not None and url is not None:
            raise Exception
        self.filename = filename
        self.url = url
        self.subtune = subtune
        self.loops = loops
        self.fileid = fileid

    def __repr__(self):
        return 'Song - filename: %s, url: %s'%(self.filename, self.url)


class QueueItem(object):
    def __init__(self, songs=[]):
        self.songs = songs

    def __repr__(self):
        return 'QueueItem - songs: %d'%(len(self.songs))


class EnqueueRequest(object):
    def __init__(self, username, queueitems=[]):
        self.username = username
        self.queueitems = queueitems

    def __repr__(self):
        return 'EnqueueRequest - user: %s, items: %d'%(self.username, len(self.queueitems))

class SongSchema(Schema):
    filename = fields.Str(missing=None)
    url = fields.Str(missing=None, allow_none=True)
    subtune = fields.Int(missing=None)
    loops = fields.Int(missing=None)
    fileid = fields.Str(missing=None, required=False)

    @marshmallow.post_load
    def make_song(self, data):
        return Song(**data)

    
class QueueItemSchema(Schema):
    songs = fields.Nested(SongSchema, many=True)

    @marshmallow.post_load
    def make_queueitem(self, data):
        return QueueItem(**data)

    
class EnqueueRequestSchema(Schema):
    username = fields.Str(missing=None)
    queueitems = fields.Nested(QueueItemSchema, many=True)

    @marshmallow.post_load
    def make_enqueuerequest(self, data):
        return EnqueueRequest(**data)
