import subprocess
import threading
import signal

# File types that can be handled by this backend (python regexp format)
regexps = [".*Vorbis audio.*"]

class Player(object):
    def __init__(self, filename, subtune, loops, stop_callback = None):
        self.filename = filename
        self.proc = None
        self.stopped = False
        self.stop_callback = stop_callback
        
    def play(self, block=False):
        self.proc = subprocess.Popen(["/usr/bin/ogg123", self.filename])
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
