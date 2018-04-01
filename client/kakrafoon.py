#!/usr/bin/python3

import argparse
import configparser
import getpass
import urllib.parse
import random
import os
import sys

import kaklib
import kakmsg.enqueue

def print_queue(queue):
    if queue.current_song and queue.items:
        while queue.items[0].songs and queue.items[0].songs[0].key != queue.current_song:
            queue.items[0].songs.pop(0)

    if not queue.playing:
        print("Kakrafoon is paused\n")
    if not queue.items:
        print("Oh noes, the queue is empty.")
    else:
        for i in queue.items:
            for s in i.songs:
                print("%04d.%02d  %-10s  %-55s" % (i.key, s.key, i.user, s.filename))

def print_volume(volume):
    for mixer in volume.mixers:
        print(mixer.name)
        for channel in mixer.channels:
            print("  %-16s %d" % (channel.name, channel.volume))


class VolumeString(object):
    """Parses arguments passed with the volume flag"""
    def __init__(self, string):
        if string.isnumeric():
            self.mixer = None
            self.channel = None
            self.volume = int(string)
        else:
            if string.count('=') == 1:
                [lvalue, vol] = string.split('=')
                if not vol.isnumeric():
                    raise TypeError('Bad volume string')
                self.volume = vol
                if '/' not in lvalue:
                    if lvalue in ['front-left', 'front-right']:
                        self.mixer = None
                        self.channel = lvalue
                    else:
                        self.mixer = lvalue
                        self.channel = None
                elif lvalue.count('/') == 1:
                    [mixer, channel] = lvalue.split('/')
                    self.mixer = mixer
                    self.channel = channel
                else:
                    raise TypeError('Bad volume string')
            else:
                raise TypeError('Bad volume string')


if __name__ == '__main__':
    parser1 = argparse.ArgumentParser(add_help=False)
    parser1.add_argument('-c', '--config', metavar='FILE',
                         help='specify config file')
    args, remaining_argv = parser1.parse_known_args()

    homedir = os.path.expanduser('~')
    config = configparser.ConfigParser()
    configfiles = [os.path.join(homedir, '.config', 'kakrafoon'),
                   os.path.join(homedir, '.kakrafoon')]
    used_config = None
    if args.config:
        try:
            f = open(args.config, 'r')
            r = config.read_file(f)
            used_config = args.config
        except:
            print('Bad configuration file')
            sys.exit(-1)
    else:
        for cf in configfiles:
            try:
                with open(cf, 'r') as f:
                    r = config.read_file(f)
                    used_config = cf
                    break
            except:
                pass

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
                        help='skip current queue entry')
    group1.add_argument('-K', '--skip-item', action='store_true',
                        help='skip current item')
    parser.add_argument('-l', '--loops', type=int, nargs='*', metavar='N',
                        help='the number of times to loop the song')
    group1.add_argument('-v', '--volume', nargs='?', metavar='V', action='append',
                        type=VolumeString,
                        help='get or set the volume - V is either volume, channel=volume,'
                        + ' mixer=volume, or mixer/channel=volume' )
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
    parser.add_argument('--verbose', action='store_true',
                        help='be more verbose')
    parser.add_argument('filename', nargs='*', metavar='FILENAME',
                        help='path and/or filename to queue')
    args = parser.parse_args(remaining_argv)

    url = args.server
    username = args.user or getpass.getuser()
    client = kaklib.Client(url, username)

    if args.verbose:
        if used_config:
            print('Using configuration file: ' + used_config)

    try:
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
        elif args.skip_item:
            client.skip_item()
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
            volume_printed = False
            for v in args.volume:
                if v is None:
                    if not volume_printed:
                        volume = client.get_volume()
                        if volume:
                            print_volume(volume)
                            volume_printed = True
                else:
                    client.set_volume(v.volume, channel=v.channel, mixer=v.mixer)
        else:
            parser.print_help()
    except kaklib.ErrorResponse as e:
        print(e.message)
    except kaklib.ConnectionError as e:
        print("Connection failed, server %s, user %s"%(client.server_url, client.username))
