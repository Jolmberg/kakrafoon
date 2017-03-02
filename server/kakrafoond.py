#!/usr/bin/python3

import os
import kakmsg.enqueue
import kakmsg.queue
import kakqueue
import songpool
import control
from flask import Flask, request
app = Flask(__name__)

kqueue = kakqueue.Queue()
kpool = songpool.SongPool()
control = control.Control(kpool, kqueue)

control.start()


os.makedirs("/tmp/kakrafoon", exist_ok=True)

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
        print(enqueue_request)

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
    q = kakmsg.queue.Queue([kpool.get_item(x) for x in kqueue.get_all()])
    schema = kakmsg.queue.QueueSchema()
    json = schema.dumps(q)
    return json.data


@app.route('/queue/<qid>', methods=['DELETE'])
def queue_delete(qid):
    kqueue.dequeue(int(qid))
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
    control.skip()
    return ''

if __name__ == '__main__':
    app.debug=True
    app.run(host='0.0.0.0')
