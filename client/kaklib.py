#!/usr/bin/python3

import json
import os
import requests
import kakmsg.enqueue
import kakmsg.error
import kakmsg.queue
import kakmsg.stats
import kakmsg.volume
import werkzeug

class ErrorResponse(Exception):
    def __init__(self, message, error_code):
        super(ErrorResponse, self).__init__(message)
        self.message = message
        self.error_code = error_code

class ConnectionError(Exception):
    pass

def raise_response_error(response):
    schema = kakmsg.error.ErrorSchema()
    err = schema.loads(response.text).data
    raise ErrorResponse(err.message, err.error_code)


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
                song.filename = os.path.basename(song.filename).encode('utf-8','replace').decode()
                secure_filename = werkzeug.secure_filename(song.filename)
                files.append((song.fileid, (secure_filename, open(realname, 'rb'))))
                i += 1

        enqueuerequest = kakmsg.enqueue.EnqueueRequest(self.username, items)
        schema = kakmsg.enqueue.EnqueueRequestSchema()
        j = schema.dumps(enqueuerequest)

        try:
            r = requests.post(self.server_url + '/queue', data={'enqueue_request':j}, files=files)
            if r.status_code == 200:
                return
            else:
                raise_error_response(r)
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def dequeue(self, item_id, song_id=None):
        """Dequeue item/song"""
        id = str(item_id) + (('/' + str(song_id)) if song_id else '')
        r = requests.delete(self.server_url + '/queue/' + id)
        if r.status_code != 200:
            raise_response_error(r)

    def get_queue(self):
        """Retrieve the current queue"""
        try:
            r = requests.get(self.server_url+ '/queue')
            schema = kakmsg.queue.QueueSchema()
            q = schema.loads(r.text).data
            return q
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def pause(self):
        """Pause playback"""
        try:
            r = requests.post(self.server_url + '/pause')
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def resume(self):
        """Resume playback"""
        try:
            r = requests.post(self.server_url + '/resume')
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def skip(self):
        """Skip current song"""
        try:
            r = requests.post(self.server_url + '/skip')
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def skip_item(self):
        """Skip current item"""
        try:
            r = requests.post(self.server_url + '/skip_item')
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def get_volume(self):
        """Get current volume"""
        try:
            r = requests.get(self.server_url + '/volume')
            schema = kakmsg.volume.VolumeSchema()
            v = schema.loads(r.text).data
            return v
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError() from e

    def set_volume(self, volume, channel=None, mixer=None, relative=False):
        """Set volume"""
        try:
            if relative:
                current = self.get_volume()
                current_mixer = None
                current_channel = None
                if mixer is None:
                    current_mixer = current.mixers[0]
                else:
                    for m in current.mixers:
                        if m.name == mixer:
                            current_mixer = m
                if current_mixer is None:
                    return False
                if channel is None:
                    # Are all channels the same? If so we need only one request.
                    if all(c.volume==current_mixer.channels[0].volume for c in current_mixer.channels):
                        old_volume = current_mixer.channels[0].volume
                        return self.set_volume(old_volume + volume, channel, mixer, False)
                    else:
                        for c in current_mixer.channels:
                            old_volume = c.volume
                            self.set_volume(old_volume + volume, c.name, mixer, False)
                        return
                else:
                    for c in current_mixer.channels:
                        if c.name == channel:
                            current_channel = c
                    if current_channel is None:
                        return False
                    old_volume = current_channel.volume
                    return self.set_volume(old_volume + volume, channel, mixer, False)

            setrequest = kakmsg.volume.SetRequest(volume, channel, mixer)
            schema = kakmsg.volume.SetRequestSchema()
            j = schema.dumps(setrequest)
            r = requests.post(self.server_url + '/volume', data={'volume_set_request':j})
            if r.status_code != 200:
                raise_response_error(r)

        except requests.exceptions.ConnectionError:
            raise ConnectionError()

    def stats_songs_by_plays(self, limit=10):
        r = requests.get(self.server_url + '/stats/songs_by_plays')
        return json.loads(r.text)

    def stats(self, metric, user=None, song=None, limit=None, reverse=False):
        url = None
        if user is not None:
            userid = str(user)
            if not userid.isnumeric():
                r = requests.get(self.server_url + '/stats/users?username=' + user)
                schema = kakmsg.stats.UserSchema()
                u = schema.loads(r.text).data
                userid = str(u.id)
            url = '/stats/users/%s/' % (userid)
        elif song is not None:
            url = '/stats/songs/%s/' % (song)
        else:
            url = '/stats/'
        url += metric
        vars = []
        if type(limit) is int and limit > 0:
            vars.append('limit=%d' % (limit,))
        if reverse:
            vars.append('reverse=true')
        if vars:
            url += '?' + '&'.join(vars)
        r = requests.get(self.server_url + url)
        return json.loads(r.text)
