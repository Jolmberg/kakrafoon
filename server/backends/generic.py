import subprocess
import threading
import signal

# File types that can be handled by this backend (python regexp format)
regexps = {
    '.*Vorbis audio.*' : ('ogg123', ['/usr/bin/ogg123'], None, None),
    '.*PlaySID.*' : ('sidplay2', ['/usr/bin/aoss', '/usr/bin/padsp', '/usr/bin/sidplay2', '-os'],
                     '-o$s', None),
    '.*NES Sound File.*' : ('nosefart', ['/usr/bin/nosefart', '-l 1200]'], '-t $s', '-a $l'),
    '.*MPEG.*' : ('mplayer', ['/usr/bin/mplayer'], None, None)
}

class Player(object):
    def __init__(self, regexp, filename, subtune, loops, stop_callback = None):
        self.subtune = subtune
        self.loops = loops
        self.filename = filename
        self.proc = None
        self.stopped = False
        self.stop_callback = stop_callback

        n, c, s, l = regexps[regexp]
        self.name = n
        self.cmd = c[:]
        print(self.cmd)
        if subtune:
            self.cmd.append(s.replace('$s', str(subtune)))
        if loops:
            self.cmd.append(s.replace('$l', str(loops)))
        print(self.cmd)
        self.cmd.append(self.filename)
        
    def play(self, block=False):
        print(self.cmd)
        self.proc = subprocess.Popen(self.cmd)
        if block:
            self.proc.wait()
            self.proc = None
            self.stopped = True
        else:
            self.thread = threading.Thread(target=self._wait)
            self.thread.run()

    # These methods should be supported by a good backend.
    def pause(self):
        if self.proc:
            self.proc.send_signal(signal.SIGSTOP)

    def resume(self):
        if self.proc:
            self.proc.send_signal(signal.SIGCONT)

    def abort(self):
        if self.proc:
            self.proc.send_signal(signal.SIGCONT)
            self.proc.send_signal(signal.SIGTERM)

    def _wait(self):
        self.proc.wait()
        self.proc = None
        self.stopped = True
        if self.stop_callback:
            self.stop_callback()


def get_player(regexp, filename, subtune, loops, stop_callback = None):
    return Player(regexp, filename, subtune, loops, stop_callback)
