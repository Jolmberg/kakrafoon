import subprocess
import threading

# File types that can be handled by this backend (python regexp format)
regexps = [".*Vorbis audio.*"]

class Player(object):
    def __init__(self, filename, subtune, loops, stop_callback = None):
        self.filename = filename
        self.proc = None
        self.stopped = False
        self.stop_callback = stop_callback
        
    def play(self):
        self.proc = subprocess.Popen(["/usr/bin/ogg123", self.filename])
        self.thread = threading.Thread(target=self._wait)
        self.thread.run()

    # These methods should be supported by a good backend.
    # def pause():
    #     pass

    # def unpause():
    #     pass

    # def stop():
    #     pass

    def _wait(self):
        self.proc.wait()
        self.stopped = True
        if self.stop_callback:
            self.stop_callback()
