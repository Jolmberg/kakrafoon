import subprocess
import threading
import signal

# File types that can be handled by this backend (python regexp format)
regexps = {
    '.*Vorbis audio.*' : ('ogg123', ['/usr/bin/ogg123'], None, None),
    '.*PlaySID.*' : ('sidplay2', ['/usr/bin/sidplay2', '-os'], '-o$s', None),
    '.*NES Sound File.*' : ('nosefart', ['/usr/bin/nosefart', '-l 1200', '-a 2'], '-t $s', '-a $l'),
    '.*(Fastt|ScreamT|Prot)racker.*' : ('mikmod', ['/usr/bin/mikmod', '-hq', '-q'], None, None),
    '.*MPEG.*' : ('mplayer', ['/usr/bin/mplayer'], None, None)
}

class Player(object):
    def __init__(self, regexp, filename, subtune, loops):
        self.subtune = subtune
        self.loops = loops
        self.filename = filename
        self.proc = None
        self.stopped = False

        n, c, s, l = regexps[regexp]
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
        try:
            self.proc.send_signal(signal.SIGSTOP)
            return True
        except:
            return False

    def resume(self):
        try:
            self.proc.send_signal(signal.SIGCONT)
            return True
        except:
            return False

    def abort(self):
        try:
            self.proc.send_signal(signal.SIGCONT)
            self.proc.send_signal(signal.SIGTERM)
            return True
        except:
            return False


def get_player(regexp, filename, subtune, loops):
    return Player(regexp, filename, subtune, loops)
