#!/usr/bin/python3

import os
import requests
import kakmsg.enqueue
import kakmsg.error
import kakmsg.queue
import kakmsg.volume
import werkzeug


class ErrorResponse(Exception):
    def __init__(self, message, error_code):
        super(ErrorResponse, self).__init__(message)
        self.message = message
        self.error_code = error_code


def raise_response_error(response):
    schema = kakmsg.error.ErrorSchema()
    err = schema.loads(response.text).data
    raise ErrorResponse(err.message, err.error_code)


class Client(object):
    def __init__(self, url, username):
        self.server_url = url
        self.username = username

    def connection_error(self):
        print("Connection failed, server %s, user %s"%(self.server_url, self.username))

    def enqueue(self, items):
        files = []
        i = 0
        for item in items:
            for song in item.songs:
                song.fileid = 'f' + str(i).zfill(7)
                realname = song.filename
                song.filename = os.path.basename(song.filename).encode('utf-8','replace').decode()
                secure_filename = werkzeug.secure_filename(song.filename)
                files.append((song.fileid, (secure_filename, open(realname, 'rb'))))
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
            self.connection_error()

    def dequeue(self, items):
        """Dequeue item(s)"""
        if len(items) == 1:
            r = requests.delete(self.server_url + '/queue/' + items[0])
            if r.status_code != 200:
                raise_response_error(r)
        else:
            print("Multi-delete not supported yet")

    def get_queue(self):
        """Retrieve the current queue"""
        try:
            r = requests.get(self.server_url+ '/queue')
            schema = kakmsg.queue.QueueSchema()
            q = schema.loads(r.text).data
            return q
        except requests.exceptions.ConnectionError:
            self.connection_error()

    def pause(self):
        """Pause playback"""
        try:
            r = requests.post(self.server_url + '/pause')
        except requests.exceptions.ConnectionError:
            self.connection_error()

    def resume(self):
        """Resume playback"""
        try:
            r = requests.post(self.server_url + '/resume')
        except requests.exceptions.ConnectionError:
            self.connection_error()

    def skip(self):
        """Skip current song"""
        try:
            r = requests.post(self.server_url + '/skip')
        except requests.exceptions.ConnectionError:
            self.connection_error()

    def get_volume(self):
        """Get current volume"""
        try:
            r = requests.get(self.server_url + '/volume')
            schema = kakmsg.volume.VolumeSchema()
            v = schema.loads(r.text).data
            return v
        except requests.exceptions.ConnectionError:
            self.connection_error()

    def set_volume(self, volume, channel=None, control=None):
        """Set volume"""
        try:
            setrequest = kakmsg.volume.SetRequest(volume, channel, control)
            setrequests = kakmsg.volume.SetRequests([setrequest])
            schema = kakmsg.volume.SetRequestsSchema()
            json = schema.dumps(setrequests)
            r = requests.post(self.server_url + '/volume', data={'volume_set_requests':json})
        except requests.exceptions.ConnectionError:
            self.connection_error()
