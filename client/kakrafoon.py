#!/usr/bin/python3

import argparse
import configparser
import getpass
import urllib.parse
import random
import os

import kaklib
import kakmsg.enqueue

def print_queue(queue):
    if not queue.items:
        print("Oh noes, the queue is empty.")
    for i in queue.items:
        for s in i.songs:
            print("%04d.%02d  %-10s  %-55s" % (i.key, s.key, i.user, s.filename))

def print_volume(volume):
    for control in volume.controls:
        print(control.name)
        for channel in control.channels:
            print("  %-16s %d" % (channel.name, channel.volume))


if __name__ == '__main__':
    parser1 = argparse.ArgumentParser(add_help=False)
    parser1.add_argument('-c', '--config', metavar='FILE',
                         help='specify config file')
    args, remaining_argv = parser1.parse_known_args()

    homedir = os.path.expanduser('~')
    config = configparser.ConfigParser()
    configfiles = [os.path.join(homedir, '.config', 'kakrafoon'),
                   os.path.join(homedir, '.kakrafoon')]
    if args.config:
        configfiles.insert(0, args.config)
    config.read(configfiles)
    if config.has_section('kakrafoon'):
        defaults = dict(config.items('kakrafoon'))
    else:
        defaults = {}

    parser = argparse.ArgumentParser(parents=[parser1], description='Command line client for kakrafoond')
    parser.set_defaults(**defaults)
    parser.add_argument('-b', '--blob', action='store_true',
                        help='queue all files as a single queue entry')

    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-e', '--resume', action='store_true',
                        help='resume playback')
    group1.add_argument('-f', '--shuffle', action='store_true',
                        help='shuffle songs')
    group1.add_argument('-k', '--skip', action='store_true',
                        help='skip current song')
    parser.add_argument('-l', '--loops', type=int, nargs='*', metavar='N',
                        help='the number of times to loop the song')
    group1.add_argument('-m', '--volume', nargs='?', metavar='V', action='append',
                        help='get or set the volume')
    group1.add_argument('-p', '--pause', action='store_true',
                       help='pause playback')
    group1.add_argument('-q', '--queue', action='store_true',
                        help='show the current queue')
    group1.add_argument('-r', '--remove', nargs='*', metavar='ID',
                       help='remove entry ID from the queue')
    parser.add_argument('-s', '--server', type=str, metavar='URL',
                        required = "server" not in defaults,
                        help='url of kakrafoond server')
    parser.add_argument('-t', '--subtune', type=int, nargs='*', metavar='N',
                        help='subtune to play')
    parser.add_argument('-u', '--user', type=str, metavar='USERNAME',
                        help='username to present to the server')
    parser.add_argument('filename', nargs='*', metavar='FILENAME',
                        help='path and/or filename to queue')
    args = parser.parse_args(remaining_argv)

    url = args.server
    username = args.user or getpass.getuser()
    client = kaklib.Client(url, username)

    if args.queue:
        queue = client.get_queue()
        if queue:
            print_queue(queue)
    elif args.pause:
        client.pause()
    elif args.resume:
        client.resume()
    elif args.skip:
        client.skip()
    elif args.filename:
        songs = []
        i = 0
        filenames = args.filename[:]
        if args.shuffle:
            random.shuffle(filenames)
        for f in filenames:
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
    elif args.remove:
        client.dequeue(args.remove)
    elif args.volume is not None:
        for v in args.volume:
            if v is None:
                volume = client.get_volume()
                if volume:
                    print_volume(volume)
            else:
                if v.isnumeric():
                    client.set_volume(v)
    else:
        parser.print_help()
