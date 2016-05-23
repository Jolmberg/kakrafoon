#!/usr/bin/python3

import argparse
import getpass
import urllib.parse

import kaklib
import kakmsg.enqueue

def print_queue(queue):
    if not queue.items:
        print("Oh noes, the queue is empty.")
    for i in queue.items:
        for s in i.songs:
            print("%04d.%02d  %-10s  %-55s" % (i.key, s.key, i.user, s.filename))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line client for kakrafoond')
    parser.add_argument('-b', '--blob', action='store_true',
                        help='queue all files as a single queue entry')
    parser.add_argument('-l', '--loops', type=int, nargs='*', metavar='N',
                        help='the number of times to loop the song')
    parser.add_argument('-q', '--queue', action='store_true',
                        help='show the current queue')
    parser.add_argument('-r', '--remove', metavar='ID',
                        help='remove entry ID from the queue')
    parser.add_argument('-s', '--server', type=str, metavar='URL', required=True,
                        help='url of kakrafoond server')
    parser.add_argument('-t', '--subtune', type=int, nargs='*', metavar='N',
                        help='subtune to play')
    parser.add_argument('-u', '--user', type=str, metavar='USERNAME',
                        help='username to present to the server')
    parser.add_argument('filename', nargs='*', metavar='FILENAME',
                        help='path and/or filename to queue')
    args = parser.parse_args()

    url = args.server
    username = args.user or getpass.getuser()
    client = kaklib.Client(url, username)

    if args.queue:
        queue = client.get_queue()
        print_queue(queue)
    
    elif args.filename:
        songs = []
        i = 0
        for f in args.filename:
            scheme = urllib.parse.urlparse(f).scheme
            if scheme=='':
                song = kakmsg.enqueue.Song(filename=f)
            else:
                song = kakmsg.enqueue.Song(url=f)

            try:
                song.subtune = args.subtune[i]
            except Exception:
                pass

            try:
                song.loops = args.loops[i]
            except Exception:
                pass

            songs.append(song)
            i += 1

        if args.blob:
            queueitems = [kakmsg.enqueue.QueueItem(songs)]
        else:
            queueitems = [kakmsg.enqueue.QueueItem([s]) for s in songs]

        client.enqueue(queueitems)
