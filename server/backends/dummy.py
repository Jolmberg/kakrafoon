import threading
import time

# File types that can be handled by this backend (python regexp format)
regexps = [".*"]

class Player(object):
    def __init__(self, regexp, filename, subtune, loops, stop_callback = None):
        self.filename = filename
        self.stopped = False
        self.stop_callback = stop_callback
        self.cmds = []

    def play(self, block=False):
        print("Playing")
        self.thread = threading.Thread(target=self._work)
        self.thread.start()
        if block:
            self.thread.join()
            self.proc = None
            self.stopped = True

    def pause(self):
        print("Pause")
        self.cmds.append('pause')

    def resume(self):
        print("Unpause")
        self.cmds.append('unpause')

    def abort(self):
        print("Stop")
        self.cmds.append('stop')

    def _work(self, length=60):
        left = length
        state = 'playing'
        while True:
            while self.cmds:
                cmd = self.cmds.pop(0)

                if cmd == 'pause':
                    state = 'paused'
                elif cmd == 'unpause':
                    if state == 'paused':
                        state = 'playing'
                elif cmd == 'stop':
                    break

            if state == 'playing':
                left -= 1
                print("Playing, %d seconds left" % (left,))
                if left <= 0:
                    break
            time.sleep(1)

        self.stopped = True
        if self.stop_callback:
            self.stop_callback()

def get_player(regexp, filename, subtune, loops, stop_callback=None):
    return Player(regexp, filename, subtune, loops, stop_callback)
