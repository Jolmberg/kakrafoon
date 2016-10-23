import threading
import os

import kakraplay

def wait_for_all(events):
    """Wait for all Event objects to be true.
       If any Event is false, wait for it, then check all Events again"""
    while True:
        for x in events:
            if not x.is_set():
                x.wait()
                break
        else:
            return


class Control(threading.Thread):

    def __init__(self, kpool, kqueue):
        self.pool = kpool
        self.queue = kqueue
        self.item = None
        self.song_id = 0
        self.player = None
        self.running = threading.Event()
        super(Control, self).__init__()

    def run(self):
        item_id = None
        self.running.set()
        while True:
            wait_for_all([self.running, self.queue.nonempty])
            item_id = self.queue.get_first()
            if item_id is None:
                continue
            self.item = self.pool.get_item(item_id)

            for song in self.item.songs:
                realfilename = os.path.join('/tmp/kakrafoon',str(self.item.key), str(song.key))
                print(realfilename)
                self.player = kakraplay.get_player(realfilename,
                                                   subtune=song.subtune,
                                                   loops=song.loops)
                # What if pause has been called by now!? Make this stuff thread safe!
                self.player.play()
            self.pool.remove_item(item_id)
            self.queue.pop()

    def pause(self):
        self.running.clear()
        if self.player:
            self.player.pause()

    def resume(self):
        self.running.set()
        if self.player:
            self.player.resume()

    def skip(self):
        if self.player:
            self.player.abort()
