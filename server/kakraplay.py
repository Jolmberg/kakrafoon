#!/usr/bin/env python3

import subprocess
import importlib
import argparse
import sys
import os
import re

# backend_order is the order in which backends are tried
# TODO: This should be configurable (and probably needs to express more
#       complicated things than a simple order)
backend_order = ['generic', 'dummy']

class NoBackendError(Exception):
    def __init__(self, file_output):
        self.file_output = file_output
        
class FileNotFoundError(Exception):
    pass

def sort_modules(modules):
    for name in reversed(backend_order):
        mods = [m for m in modules if m.__name__ == name]
        for m in mods:
            modules.remove(m)
            modules.insert(0, m)

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
            if hasattr(mod, 'get_player'):
                modules.append(mod)
            else:
                print('Backend "%s" has no get_player function and is worthless.' % (file))
        except:
            print('Backend %s is broken.' % (file))
    sort_modules(modules)
    return modules

def file_info(filename):
    return subprocess.check_output(['/usr/bin/file', '-b', filename]).decode()

# This is the function kakrafoond should call
def get_player(filename, subtune=None, loops=0):
    if not os.path.isfile(filename):
        raise FileNotFoundError
    
    text = file_info(filename)
    module = None
    regexp = None
    for m in modules:
        if hasattr(m, 'regexps'):
            for r in m.regexps:
                if re.match(r, text):
                    module = m
                    regexp = r
                    break
            if module is not None:
                break
    else:
        raise NoBackendError(text)
    
    return module.get_player(regexp, filename, subtune, loops)

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
    except NoBackendError as e:
        print("No suitable backend found. Output from 'file' was:\n" + e.file_output)
    except FileNotFoundError:
        print('File not found!')

