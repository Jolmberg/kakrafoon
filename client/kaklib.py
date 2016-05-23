#!/usr/bin/python3

import os
import requests
import kakmsg.enqueue
import kakmsg.queue

class Client(object):
    def __init__(self, url, username):
        self.server_url = url
        self.username = username

    def enqueue(self, items):
        files = []
        i = 0
        for item in items:
            for song in item.songs:
                song.fileid = 'f' + str(i).zfill(7)
                realname = song.filename
                song.filename = os.path.basename(song.filename)
                files.append((song.fileid, (song.filename, open(realname, 'rb'))))
                i += 1

        enqueuerequest = kakmsg.enqueue.EnqueueRequest(self.username, items)
        schema = kakmsg.enqueue.EnqueueRequestSchema()
        json = schema.dumps(enqueuerequest)

        try:
            r = requests.post(self.server_url + '/queue', data={'enqueue_request':json}, files=files)
            if r.status_code == 200:
                return
            else:
                print("Server complained with message: %s" % (r.text,))
        except requests.exceptions.ConnectionError:
            print("Connection failed")

    def get_queue(self):
        """Retrieve the current queue"""
        try:
            r = requests.get(self.server_url+ '/queue')
            schema = kakmsg.queue.QueueSchema()
            q = schema.loads(r.text).data
            return q
        except requests.exceptions.ConnectionError:
            print("Connection failed")
