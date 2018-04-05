import threading
import os
import stopwatch
import kakraplay

def synchronised(f):
    """Synchronisation decorator"""

    def real_function(*args, **kw):
        args[0].lock.acquire()
        try:
            return f(*args, **kw)
        finally:
            args[0].lock.release()
    return real_function


class Control(threading.Thread):

    def __init__(self, kpool, kqueue):
        self.lock = threading.Lock()
        self.pool = kpool
        self.queue = kqueue
        self.item = None
        self.songs = []
        self.song = None
        self.paused = False
        self.player = None
        self.playing = False
        self.stopwatch = None
        self.running = threading.Event()
        self.skip_current_item = False
        self.skip_current_song = False
        self.stopwatch = stopwatch.StopWatch()
        super(Control, self).__init__()

    @synchronised
    def _get_next(self):
        if len(self.songs) > 1:
            self.songs.pop(0)
        else:
            if self.item:
                self.pool.remove_item(self.item.key)
                self.queue.pop()
            self.song = None
            self.songs = []
            self.item = None
            item_id = self.queue.get_first()
            if item_id is None:
                return False
            self.item = self.pool.get_item(item_id)
            self.songs = self.item.songs
        print(self.songs)
        self.song = self.songs[0]
        realfilename = os.path.join('/tmp/kakrafoon', str(self.item.key), str(self.song.key))
        print(realfilename)
        self.player = kakraplay.get_player(realfilename,
                                           subtune=self.song.subtune,
                                           loops=self.song.loops)
        self.stopwatch.reset()
        return True

    def run(self):
        self.running.set()
        while True:
            if self._get_next() == False:
                self.queue.nonempty.wait()
                continue

            if self.paused:
                self.running.clear()
            self.running.wait()

            self.lock.acquire()
            if self.skip_current_song:
                self.skip_current_song = False
                self.lock.release()
                continue
            if self.skip_current_item:
                self.skip_current_item = False
                self.songs = []
                self.lock.release()
                continue
            self.lock.release()

            self.playing = True
            self.stopwatch.start()
            self.player.play()
            self.stopwatch.pause()
            self.playing = False

            self.lock.acquire()
            self.skip_current_song = False
            if self.skip_current_item:
                self.skip_current_item = False
                self.songs = []
            self.lock.release()

    @synchronised
    def pause(self):
        if self.paused:
            return
        self.paused = True
        self.running.clear()
        if self.playing:
            self.player.pause()
            self.stopwatch.pause()

    @synchronised
    def resume(self):
        if not self.paused:
            return
        self.paused = False
        self.running.set()
        if self.playing:
            self.player.resume()
            self.stopwatch.resume()

    @synchronised
    def skip_song(self):
        if self.item:
            self.skip_current_song = True
            if self.playing:
                self.player.abort()
            if not self.running.is_set():
                self.running.set()

    @synchronised
    def skip_item(self):
        if self.item:
            self.skip_current_item = True
            if self.playing:
                self.player.abort()
            if not self.running.is_set():
                self.running.set()

    @synchronised
    def is_playing(self):
        return not self.paused
