#!/usr/bin/python3

import subprocess
import importlib
import argparse
import sys
import os
import re

class NoBackendError(Exception):
    def __init__(self, file_output):
        self.file_output = file_output
        
class FileNotFoundError(Exception):
    pass

def load_backends(dir):
    modules=[]
    for file in os.listdir(dir):
        if file.startswith('.') or file == '__pycache__':
            continue
        if os.path.isfile(os.path.join(dir,file)):
            if file.endswith('.py'):
                file = file[:-3]
            else:
                continue
        try:
            mod = importlib.import_module(file)
            if hasattr(mod, 'Player'):
                modules.append(mod)
            else:
                print('Backend "%s" has no Player class and is worthless.' % (file))
        except:
            print('Backend %s is broken.' % (file))
    return modules

def file_info(filename):
    return subprocess.check_output(['/usr/bin/file', '-b', filename]).decode()

# This is the function kakrafoond should call
def get_player(filename, subtune=None, loops=0, stop_callback=None):
    if not os.path.isfile(args.filename):
        raise FileNotFoundError
    
    text = file_info(args.filename)
    module = None
    for m in modules:
        if hasattr(m, 'regexps'):
            for r in m.regexps:
                if re.match(r, text):
                    module = m
    if not module:
        raise NoBackendError(text)
    
    return m.Player(filename, subtune, loops, stop_callback)

# TODO: Make path configurable (and also not relative to .)
sys.path.append('./backends')
modules = load_backends('./backends')

# If we are being executed as a stand-alone program:
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Play sound and/or music.')
    parser.add_argument('-s', '--subtune', type=int, metavar='s', default=-1,
                        help='the subtune to play')
    parser.add_argument('-l', '--loops', type=int, metavar='n', default=0,
                        help='the number of times to loop the song')
    parser.add_argument('filename', help='path and/or filename to play')
    args = parser.parse_args()

    try:
        p = get_player(args.filename, args.subtune, args.loops)
        p.play()
        # TODO: Handle user input istead of just waiting here...
        p.proc.wait()
    except NoBackendError as e:
        print("No suitable backend found. Output from 'file' was:\n" + e.file_output)
    except FileNotFoundError:
        print('File not found!')

