#!/usr/bin/python3

import uuid
import os
import kakmsg.enqueue
import kakmsg.queue
import kakqueue
from flask import Flask, request
app = Flask(__name__)

kqueue = kakqueue.Queue()
items = {}
songs = {}
item_counter = 0

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


def save_file(item_id, file_id, fileobj):
    path = os.path.join('/tmp/kakrafoon', str(item_id))
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, str(file_id))
    fileobj.save(filepath)


@app.route('/queue', methods=['POST'])
def queue_add():
    """Add items to the queue

    Request can optionally contain an enqueue_request parameter.
    Otherwise, each file posted is queued as a separate item.
    """
    global item_counter
    request_id = str(uuid.uuid4())
    to_play = []
    enqueue_request = None
    if 'enqueue_request' in request.form:
        schema = kakmsg.enqueue.EnqueueRequestSchema()
        enqueue_request = schema.loads(request.form['enqueue_request']).data
        print(enqueue_request)

    new_items = []
    claimed_files = set()
    if enqueue_request:
        for enqueue_item in enqueue_request.queueitems:
            item_counter += 1
            print("Item " + str(item_counter))
            item = kakmsg.queue.QueueItem(item_counter,
                                          enqueue_request.username)
            song_counter = 0
            for enqueue_song in enqueue_item.songs:
                print("Song " + str(song_counter))
                fileid = enqueue_song.fileid
                if fileid not in request.files:
                    print("bapp")
                    continue
                claimed_files.add(fileid)
                fobj = request.files[fileid]
                filename = os.path.split(fobj.filename)[1]
                song_counter += 1
                song = make_song(song_counter, enqueue_song=enqueue_song)
                save_file(item_counter, song_counter, fobj)
                item.songs.append(song)

            if song_counter>0:
                items[item_counter] = item
                new_items.append(item_counter)

    # Handle files that were not mentioned in the json payload
    if len(request.files) > len(claimed_files):
        for id, fobj in request.files:
            if id not in claimed_files:
                item_counter += 1
                print("Item " + str(item_counter))
                item = kakmsg.queue.QueueItem(item_counter,
                                              enqueue_request.username)
                filename = os.path.split(fobj.filename)[1]
                save_file(item_counter, 0, fobj)
                song = make_song(0, filename=filename)
                item.songs.append(song)
                new_items.append(item_counter)
                items[item_counter] = item

    for item_id in new_items:
        item = items[item_id]
        kqueue.enqueue(item_id, item.user, len(item.songs))
                
    print(items)
    print(enqueue_request)
    print('%d new item(s) added' % len(new_items))
    return ''


@app.route('/queue', methods=['GET'])
def queue_show():
    """Return the current queue as a queue.Queue object"""
    q = kakmsg.queue.Queue([items[x] for x in kqueue.get_all()])
    schema = kakmsg.queue.QueueSchema()
    json = schema.dumps(q)
    return json.data


@app.route('/queue/<qid>', methods=['DELETE'])
def queue_delete(qid):
    print('Deleting item ' + qid + ' from queue.')

if __name__ == '__main__':
    app.debug=True
    app.run()
