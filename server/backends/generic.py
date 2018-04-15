import re
import signal
import subprocess
import threading
import time
from collections import OrderedDict

# File types that can be handled by this backend (python regexp format)
regexps = OrderedDict([
    ('.*Vorbis audio.*', ('ogg123', ['ogg123'], None, None)),
    ('.*PlaySID.*', ('sidplay2', ['sidplay2', '-os'], '-o$s', None)),
    ('.*NES Sound File.*', ('nosefart', ['nosefart', '-l 1200', '-a 2'], '-t $s', '-a $l')),
    ('.*(Fastt|ScreamT|Impulse T|Prot)racker.*', ('mikmod', ['mikmod', '-hq', '-q'], None, None)),
    ('.*MPEG.*', ('mplayer', ['mplayer'], None, None)),
    ('.*', ('mplayer', ['mplayer'], None, None))
])

class Player(object):
    def __init__(self, regexp, filename, subtune, loops, text):
        self.subtune = subtune
        self.loops = loops
        self.filename = filename
        self.text = text
        self.proc = None
        self.stopped = False

        n, c, s, l = regexps[regexp]

        self._is_loopable = l is not None
        self._has_subtunes = s is not None
        self.name = n
        self.cmd = c[:]
        print(self.cmd)
        if subtune and s:
            self.cmd.append(s.replace('$s', str(subtune)))
        if loops and l:
            self.cmd.append(l.replace('$l', str(loops)))
        print(self.cmd)
        self.cmd.append(self.filename)
        
    def play(self):
        print(self.cmd)
        self.proc = subprocess.Popen(self.cmd)
        self.proc.wait()
        self.proc = None
        self.stopped = True

    # These methods should be supported by a good backend.
    def pause(self):
        if self.proc is None:
            return False
        try:
            self.proc.send_signal(signal.SIGSTOP)
            return True
        except:
            return False

    def resume(self):
        if self.proc is None:
            return False
        try:
            self.proc.send_signal(signal.SIGCONT)
            return True
        except:
            return False

    def abort(self):
        if self.proc is None:
            return False
        try:
            self.proc.send_signal(signal.SIGCONT)
            self.proc.send_signal(signal.SIGTERM)
            threading.Thread(target=sigkill, args=(self.proc,)).start()
            return True
        except:
            return False

    def is_loopable(self):
        return self._is_loopable

    def has_subtunes(self):
        return self._has_subtunes

    def get_subtune(self):
        if not self._has_subtunes:
            return None
        if self.subtune:
            return self.subtune

        if self.name == 'sidplay2':
            m = re.search('default song: (\\d)', self.text)
            if m:
                ds = m.groups()[0]
                return int(ds)
            else:
                return 1

        if self.name == 'nosefart':
            return 1


def get_player(regexp, filename, subtune, loops, text):
    return Player(regexp, filename, subtune, loops, text)

def sigkill(proc):
    time.sleep(5)
    if proc.poll() is None:
        # This is not normal and should be logged
        proc.send_signal(signal.SIGKILL)
