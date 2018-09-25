#!/usr/bin/env python3

import json
import os
import kakmsg.enqueue
import kakmsg.queue
import kakmsg.volume
import kakmsg.error
import kakmsg.stats
import kakqueue
import songpool
import control
import volume
import stats
from flask import Flask, request
app = Flask(__name__)

kqueue = kakqueue.Queue()
kstats = stats.Stats()
kpool = songpool.SongPool(kstats)
control = control.Control(kpool, kqueue, kstats)

control.start()

def make_song(key, filename=None, url=None, enqueue_song=None):
    """Create a kakmsg.queue.Song object from whatever info is available"""
    song = kakmsg.queue.Song(key=key)
    if enqueue_song:
        song.filename = enqueue_song.filename
        song.url = enqueue_song.url
        song.subtune = enqueue_song.subtune
        song.loops = enqueue_song.loops
    elif filename:
        song.filename = filename
    elif url:
        song.url = url
    else:
        return None
    return song


def make_error(http_code, error_code, msg):
    err = kakmsg.error.Error(error_code, msg)
    schema = kakmsg.error.ErrorSchema()
    j = schema.dumps(err)
    return (j.data, http_code, { 'Content-Type' : 'application/json' })


@app.route('/queue', methods=['POST'])
def queue_add():
    """Add items to the queue

    Request can optionally contain an enqueue_request parameter.
    Otherwise, each file posted is queued as a separate item.
    """
    enqueue_request = None
    if 'enqueue_request' in request.form:
        schema = kakmsg.enqueue.EnqueueRequestSchema()
        enqueue_request = schema.loads(request.form['enqueue_request']).data

    new_items = []
    claimed_files = set()
    if enqueue_request:
        for enqueue_item in enqueue_request.queueitems:
            # Make sure this item has at least one song
            for enqueue_song in enqueue_item.songs:
                if enqueue_song.fileid in request.files:
                    break
            else:
                continue

            item = kakmsg.queue.QueueItem(enqueue_request.username)
            item.song_counter = 0
            for enqueue_song in enqueue_item.songs:
                fileid = enqueue_song.fileid
                if fileid not in request.files:
                    continue
                claimed_files.add(fileid)
                fobj = request.files[fileid]
                filename = os.path.split(fobj.filename)[1]
                item.song_counter += 1
                song = make_song(item.song_counter, enqueue_song=enqueue_song)
                song.file_object = fobj
                item.songs.append(song)

            item_id = kpool.add_item(item)
            new_items.append(item_id)

    # Handle files that were not mentioned in the json payload
    if len(request.files) > len(claimed_files):
        for id, fobj in request.files:
            if id not in claimed_files:
                item = kakmsg.queue.QueueItem(enqueue_request.username)
                filename = os.path.split(fobj.filename)[1]
                song = make_song(0, filename=filename)
                item.songs.append(song)
                item_id = kpool.add_item(item)
                new_items.append(item_id)

    for item_id in new_items:
        item = kpool.get_item(item_id)
        kqueue.enqueue(item_id, item.user, len(item.songs))
                
    print("Pool: " + str(kpool.items))
    print('%d new item(s) added' % len(new_items))
    return ''

@app.route('/queue', methods=['GET'])
def queue_show():
    """Return the current queue as a queue.Queue object"""
    current_song = None
    current_song_time = None
    if control.song:
        current_song = control.song.key
        current_song_time = control.stopwatch.read()
        print(current_song_time)
    playing = control.is_playing()
    q = kakmsg.queue.Queue([kpool.get_item(x) for x in kqueue.get_all()],
                           playing, current_song, current_song_time)
    schema = kakmsg.queue.QueueSchema()
    j = schema.dumps(q)
    return j.data

@app.route('/queue/<item_id>', methods=['DELETE'])
def queue_delete_item(item_id):
    item_id = int(item_id)
    if item_id == kqueue.get_first():
        msg = 'Cannot dequeue the first item in the queue, try skipping instead.'
        return make_error(400, 1, msg)

    kqueue.dequeue(item_id)
    kpool.remove_item(item_id)
    return ''

@app.route('/queue/<item_id>/<song_id>', methods=['DELETE'])
def queue_delete_song(item_id, song_id):
    item_id = int(item_id)
    song_id = int(song_id)
    if item_id == kqueue.get_first():
        msg = 'Cannot dequeue anything within the first item in the queue, try skipping instead.'
        return make_error(400, 2, msg)
    item = kpool.get_item(item_id)
    if len(item.songs) == 1:
        kqueue.dequeue(item_id)
        kpool.remove_item(item_id)
    else:
        kpool.remove_song(item_id, song_id)
    return ''

@app.route('/pause', methods=['POST'])
def pause():
    control.pause()
    return ''

@app.route('/resume', methods=['POST'])
def resume():
    control.resume()
    return ''

@app.route('/skip', methods=['POST'])
def skip():
    control.skip_song()
    return ''

@app.route('/skip_item', methods=['POST'])
def skip_item():
    control.skip_item()
    return ''

@app.route('/volume', methods=['GET'])
def volume_get():
    vol = volume.get_all()
    v = kakmsg.volume.Volume([kakmsg.volume.Mixer(name, [kakmsg.volume.Channel(name, x)
                                                         for (name, x) in channels.items()])
                              for (name, channels) in vol.items()])
    schema = kakmsg.volume.VolumeSchema()
    j = schema.dumps(v)
    return j.data

@app.route('/volume', methods=['POST'])
def volume_set():
    if 'volume_set_request' in request.form:
        schema = kakmsg.volume.SetRequestSchema()
        r = schema.loads(request.form['volume_set_request']).data
        try:
            volume.set(r.volume, r.channel, r.mixer)
        except volume.NoSuchMixerError:
            return make_error(400, 2000, 'No such mixer.')
        except volume.NoSuchChannelError:
            return make_error(400, 2001, 'No such channel.')
        except:
            return make_error(500, 2002, 'Unknown mixer error.')
        return ''

@app.route('/stats/songs/<songid>', methods=['GET'])
def stats_song(songid):
    song = kstats.get_song_by_column('id', songid)
    if song is None:
        return make_error(404, 3000, 'Song not found')
    s = kakmsg.stats.Song(*song)
    schema = kakmsg.stats.SongSchema()
    j = schema.dumps(s)
    return j.data

@app.route('/stats/users/<userid>', methods=['GET'])
def stats_users_by_id(userid):
    user = kstats.get_user_by_column('id', userid)
    if user is None:
        return make_error(404, 3001, 'No such user')
    s = kakmsg.stats.User(*user)
    schema = kakmsg.stats.UserSchema()
    j = schema.dumps(s)
    return j.data

@app.route('/stats/users', methods=['GET'])
def stats_users():
    if 'username' in request.args:
        username = request.args['username']
        if username is not None:
            user = kstats.get_user_by_column('username', username)
            if user is None:
                return make_error(400, 3002, 'User not found')
        s = kakmsg.stats.User(*user)
        schema = kakmsg.stats.UserSchema()
        j = schema.dumps(s)
        return j.data
    return make_error(400, 3003, 'Bad request')

def get_limit_and_reverse():
    r = {}
    if 'limit' in request.args:
        limit = request.args['limit']
        if limit.isnumeric() and int(limit) > 0:
            r['limit'] = limit
    if request.args.get('reverse', 'false') == 'true':
        r['ascending'] = True
    return r

def metric(method, args):
    kwargs = get_limit_and_reverse()
    print(kwargs)
    stuff = method(*args, **kwargs)
    return json.dumps([dict(x) for x in stuff])

@app.route('/stats/songs/<songid>/users_by_plays', methods=['GET'])
def stats_song_users_by_plays(songid):
    return metric(kstats.metric_usersongs_thing_by_value, ('user', 'plays', int(songid)))

@app.route('/stats/songs/<songid>/users_by_playtime', methods=['GET'])
def stats_song_users_by_playtime(songid):
    return metric(kstats.metric_usersongs_thing_by_value, ('user', 'playtime', int(songid)))

@app.route('/stats/users/<userid>/songs_by_plays', methods=['GET'])
def stats_user_songs_by_plays(userid):
    return metric(kstats.metric_usersongs_thing_by_value, ('song', 'plays', int(userid)))

@app.route('/stats/users/<userid>/songs_by_playtime', methods=['GET'])
def stats_user_songs_by_playtime(userid):
    return metric(kstats.metric_usersongs_thing_by_value, ('song', 'playtime', int(userid)))

@app.route('/stats/songs_by_plays', methods=['GET'])
def stats_songs_by_plays():
    return metric(kstats.metric_thing_by_value,('song', 'plays'))

@app.route('/stats/songs_by_playtime', methods=['GET'])
def stats_songs_by_playtime():
    return metric(kstats.metric_thing_by_value,('song', 'playtime'))

@app.route('/stats/songs_by_users', methods=['GET'])
def stats_songs_by_players():
    return metric(kstats.metric_usersongs_thing_by_unique_value,('song', 'users'))

@app.route('/stats/users_by_plays', methods=['GET'])
def stats_users_by_plays():
    return metric(kstats.metric_thing_by_value,('user', 'plays'))

@app.route('/stats/users_by_playtime', methods=['GET'])
def stats_users_by_playtime():
    return metric(kstats.metric_thing_by_value,('user', 'playtime'))

@app.route('/stats/users_by_songs', methods=['GET'])
def stats_users_by_songs():
    return metric(kstats.metric_usersongs_thing_by_unique_value,('user', 'songs'))

if __name__ == '__main__':
    app.debug=True
    app.run(host='0.0.0.0', threaded=True)
