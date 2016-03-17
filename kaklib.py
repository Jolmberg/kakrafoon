#!/usr/bin/python3

from marshmallow import Schema, fields
import marshmallow
import requests

class Song(object):
    def __init__(self, filename, subtune=-1, loops=0):
        self.filename = filename
        self.subtune = subtune
        self.loops = loops

        
class QueueItem(object):
    def __init__(self, songs):
        self.songs = songs


class EnqueueRequest(object):
    def __init__(self, queueitems):
        self.queueitems = queueitems
        
        
class SongSchema(Schema):
    filename = fields.Str()
    subtune = fields.Int()
    loops = fields.Int()
    filenumber = fields.Int()

    
class QueueItemSchema(Schema):
    songs = fields.Nested(SongSchema, many=True)

    
class EnqueueRequestSchema(Schema):
    queueitems = fields.Nested(QueueItemSchema, many=True)
    

class Client(object):
    def __init__(self, url, username):
        self.server_url = url
        self.username = username
    
    def enqueue(self, items):
        files = []
        i = 0
        for item in items:
            for song in item.songs:
                song.filenumber = i
                files.append(('f' + str(i).zfill(7), (song.filename, open(song.filename, 'rb'))))
                i += 1
        
        enqueuerequest = EnqueueRequest(items)
        schema = EnqueueRequestSchema()
        json = schema.dump(enqueuerequest)
        
        try:
            r = requests.post(self.server_url + '/queue', data={'json':json}, files=files)
            print(r)
        except requests.exceptions.ConnectionError:
            print("Connection failed")
