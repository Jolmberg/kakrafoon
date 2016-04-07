#!/usr/bin/python3

import os
import requests
import kakmsg

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
                realname = song.filename
                song.filename = os.path.basename(song.filename)
                files.append(('f' + str(i).zfill(7), (song.filename, open(realname, 'rb'))))
                i += 1
        
        enqueuerequest = kakmsg.EnqueueRequest(items)
        schema = kakmsg.EnqueueRequestSchema()
        json = schema.dumps(enqueuerequest)
        
        try:
            print(files)
            r = requests.post(self.server_url + '/queue', data={'json':json}, files=files)
            print(r)
        except requests.exceptions.ConnectionError:
            print("Connection failed")
