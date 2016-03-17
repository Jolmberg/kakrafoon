#!/usr/bin/python3

import argparse
import getpass
import kaklib


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

    if args.filename:
        songs = []
        i = 0
        for f in args.filename:
            song = kaklib.Song(f)
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
            queueitems = [kaklib.QueueItem(songs)]
        else:
            queueitems = [kaklib.QueueItem([s]) for s in songs]

        client.enqueue(queueitems)
