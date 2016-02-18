#!/usr/bin/python3

import argparse
import requests

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command line client for kakrafoond')
    parser.add_argument('-b', '--blob', action='store_true',
                        help='queue all files as a single queue entry')
    parser.add_argument('-l', '--loops', type=int, metavar='N',
                        help='the number of times to loop the song')
    parser.add_argument('-q', '--queue', action='store_true',
                        help='show the current queue')
    parser.add_argument('-r', '--remove', metavar='ID',
                        help='remove entry ID from the queue')
    parser.add_argument('-s', '--server', type=str, metavar='URL', required=True,
                        help='url of kakrafoond server')
    parser.add_argument('-t', '--subtune', type=int,
                        help='subtune to play')
    parser.add_argument('-u', '--user', type=int, metavar='USERNAME',
                        help='username to present to the server')
    parser.add_argument('filename', nargs='*', metavar='FILENAME',
                        help='path and/or filename to queue')
    args = parser.parse_args()

    url = args.server

    print('Trying ' + url + ' ...')

    if args.filename:
        files = []
        i = 1
        for x in args.filename:
            print(x)
            files.append(('f' + str(i).zfill(7), (x, open(x, 'rb'))))
            i += 1
        print(files)
        try:
            r = requests.post(url + '/queue', files=files)
            print(r)
        except requests.exceptions.ConnectionError:
            print("Connection failed")
