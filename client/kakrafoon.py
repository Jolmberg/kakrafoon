#!/usr/bin/env python3

import argparse
import configparser
import getpass
import urllib.parse
import random
import os
import shutil
import sys

import kaklib
import kakmsg.enqueue


def format_time(seconds):
    hours = seconds // 3600
    seconds -= hours * 3600
    minutes = seconds // 60
    seconds -= minutes * 60
    if hours > 0:
        return '%02d:%02d:%02d' % (hours, minutes, seconds)
    else:
        return '%02d:%02d' % (minutes, seconds)

def print_queue(queue, style=None):
    current_song = None
    if queue.current_song and queue.items:
        for s in queue.items[0].songs:
            if s.key == queue.current_song:
                current_song = s
        if current_song:
            while queue.items[0].songs[0].key != queue.current_song:
                queue.items[0].songs.pop(0)

    if style is None:
        style = 'fancy' if sys.stdout.isatty() else 'simple_long'

    if style == "simple_long":
        print_queue_simple(queue, False)
    elif style == "simple":
        print_queue_simple(queue, sys.stdout.isatty())
    else:
        print_queue_fancy(queue)

def print_queue_simple(queue, truncate):
    if not queue.items:
        return

    cols = 80
    if truncate:
        if sys.stdout.isatty():
            cols = shutil.get_terminal_size((80,24)).columns

    longestuser = max(len(i.user) for i in queue.items)
    longestsong = max(max(len(s.filename) for s in i.songs) for i in queue.items)
    longestid = max(max((max(4, (len(str(i.key)))) + max(2,len(str(s.key)))) for s in i.songs) for i in queue.items) + 1
    if longestid + 6 > cols:
        truncate = False

    for i in queue.items:
        for s in i.songs:
            fmt = None
            longestalloweduser = 0
            if not truncate:
                longestalloweduser = longestuser
                longestallowedsong = longestsong
                fmt = '{:04d}.{:02d}  {:{user}}  {}'
            else:
                # Allow at least one letter for the song name
                longestalloweduser = min(longestuser, cols - longestid - 5)
                longestallowedsong = min(longestsong, cols - longestid - longestalloweduser - 4)
                fmt = '{:04d}.{:02d}  {:{user}.{user}}  {:.{song}}'
            print(fmt.format(i.key, s.key, i.user, s.filename, user=longestalloweduser, song=longestallowedsong))

def print_table(columns, truncate_order, data):
    cols = 80
    truncate = True
    if sys.stdout.isatty():
        cols = shutil.get_terminal_size((80,24)).columns

    # Get max lengths for all columns
    maxlength = dict((column[0], 0) for column in columns)
    for row in data:
        for column in columns:
            c = column[0]
            if c in row:
                if c not in maxlength:
                    maxlength[c] = len(str(row[c]))
                else:
                    maxlength[c] = max(maxlength[c], len(str(row[c])))

    # Get min lengths for all columns
    minlength = {}
    for column in columns:
        c = column[0]
        m = column[1]
        if c not in truncate_order:
            minlength[c] = maxlength[c]
        else:
            minlength[c] = m

    spaces = 2 * (len(minlength) - 1)
    minwidth = sum(v for v in minlength.values()) + spaces
    width = sum(v for v in maxlength.values()) + spaces
    if minwidth <= cols:
        # Truncate if needed
        if width > cols:
            for col in truncate_order:
                gain = maxlength[col] - minlength[col]
                if width - gain > cols:
                    maxlength[col] = minlength[col]
                    width = width - gain
                else:
                    maxlength[col] = maxlength[col] - (width - cols)
                    break

    for row in data:
        line = []
        for column in columns:
            c = column[0]
            s = ''
            if c in row:
                s = str(row[c])[:maxlength[c]]
            if column[2] == 'l':
                s = s.ljust(maxlength[c], ' ')
            elif column[2] == 'r':
                s = s.rjust(maxlength[c], ' ')
            line.append(s)
        print('  '.join(line))

def print_queue_fancy(queue):
    if not queue.items:
        print("Oh noes, the queue is empty.")
    else:
        print('%s is playing:' % (queue.items[0].user))
        for s in queue.items[0].songs:
            line = s.filename
            if s.key == queue.current_song:
                if queue.current_song_time is not None:
                    current_song_time = format_time(queue.current_song_time)
                    line += ' (%s)' % (current_song_time,)
                if not queue.playing:
                    line += ' (paused)'
            print(line)

        if len(queue.items) > 1:
            if len(queue.items[0].songs) > 1:
                print('\nUp soon:')
            else:
                print('\nUp next:')
            for i in queue.items[1:]:
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
        self.relative = False
        if string.endswith('+') or string.endswith('-'):
            self.relative = string[-1]
            string = string[:-1]
        if string.isnumeric():
            self.mixer = None
            self.channel = None
            self.volume = int(string)
        else:
            if string.count('=') == 1:
                [lvalue, vol] = string.split('=')
                if not vol.isnumeric():
                    raise TypeError('Bad volume string')
                self.volume = int(vol)
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
        if self.relative:
            if self.relative == '-':
                self.volume = -self.volume
            self.relative = True


class RemoveString(object):
    """Parses argument passed with the remove flag"""
    def __init__(self, string):
        if string.isnumeric():
            self.item = int(string)
            self.song = None
        else:
            for sep in ['.', '/']:
                if string.count(sep) == 1:
                    strings = string.split(sep)
                    if all(x.isnumeric() for x in strings):
                        self.item = int(strings[0])
                        self.song = int(strings[1])
                        break
                    else:
                        raise TypeError('Bad item/song id')
            else:
                raise TypeError('Bad item/song id')

    def __repr__(self):
        return '%d %d' % (self.item, self.song)


if __name__ == '__main__':
    parser1 = argparse.ArgumentParser(add_help=False)
    parser1.add_argument('-c', '--config', metavar='FILE',
                         help='specify config file')
    args, remaining_argv = parser1.parse_known_args()

    homedir = os.path.expanduser('~')
    config = configparser.ConfigParser()
    configfiles = [os.path.join(homedir, '.config', 'kakrafoon'),
                   os.path.join(homedir, '.kakrafoon'),
                   '/etc/kakrafoon.conf']
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
    group1.add_argument('-i', '--highscore', type=str, nargs='+', metavar='I', action='append',
                        help='Show high scores, use --highscore help for more info'),
    group1.add_argument('-k', '--skip', action='store_true',
                        help='skip current song')
    group1.add_argument('-K', '--skip-item', action='store_true',
                        help='skip current queue item')
    parser.add_argument('-l', '--loops', type=int, nargs='*', metavar='N',
                        help='the number of times to loop the song')
    group1.add_argument('-v', '--volume', nargs='?', metavar='V', action='append',
                        type=VolumeString,
                        help='get or set the volume - V is either volume, channel=volume,'
                        + ' mixer=volume, or mixer/channel=volume\nsuffix volume with'
                        + ' + or - for relative changes')
    group1.add_argument('-p', '--pause', action='store_true',
                       help='pause playback')
    group1.add_argument('-q', '--queue', type=str, nargs='?', metavar='STYLE', const='',
                        help='show the current queue - STYLE can be simple, simple_long,'
                        + ' json, or fancy (default)')
    group1.add_argument('-r', '--remove', nargs=1, metavar='ID', action='append',
                        type=RemoveString,
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
        if args.queue is not None:
            style = args.queue
            if style == '':
                if 'queue' in defaults:
                    style = defaults['queue']
                else:
                    style = None
            if style == 'json':
                print(client.get_queue(json=True))
            else:
                print_queue(client.get_queue(), style)
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
            for r in args.remove:
                client.dequeue(r[0].item, r[0].song)
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
                    client.set_volume(v.volume, channel=v.channel, mixer=v.mixer, relative=v.relative)
        elif args.highscore is not None:
            args = args.highscore[-1]
            if args == ['help']:
                print("""Format: METRIC [user U] [song S] [limit N] [reverse]
 METRIC is one of songs_by_plays, songs_by_playtime, songs_by_users,
 users_by_plays, users_by_playtime, users_by_songs.
 Results can optionally be filtered to a single user or song.
 User can be given as user id or username. Song must always be song id.
 Examples:
  To list the five least played songs:
   "songs_by_plays limit 5 reverse"
  To list the ten users who have spent the most time playing song 1:
   "users_by_playtime song 1 limit 10""")
            else:
                metric = args[0]
                kwargs = {}
                args.pop(0)
                while args:
                    if args[0] == 'reverse':
                        kwargs['reverse'] = True
                    else:
                        kwargs[args[0]] = args[1]
                        args.pop(0)
                    args.pop(0)
                if 'limit' in kwargs:
                    kwargs['limit'] = int(kwargs['limit'])

                data = client.stats(metric, **kwargs)
                variable_column = metric.split('_')[-1]
                if variable_column == 'playtime':
                    for row in data:
                        if 'playtime' in row:
                            row['playtime'] = format_time(row['playtime'])
                songoruser = metric.split('_')[0][:-1] + 'name'
                print_table([(songoruser,1,'l'), (variable_column,-1,'r')], [songoruser], data)
        else:
            parser.print_help()
    except kaklib.ErrorResponse as e:
        print(e.message)
    except kaklib.ConnectionError as e:
        print("Connection failed, server %s, user %s"%(client.server_url, client.username))
