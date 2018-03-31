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
        self.song = None
        self.player = None
        self.running = threading.Event()
        self.skip_current_item = False
        super(Control, self).__init__()

    def run(self):
        item_id = None
        self.running.set()
        while True:
            self.item = None
            wait_for_all([self.queue.nonempty])
            # The first item cannot be dequeued so we can assume that it exists here:
            item_id = self.queue.get_first()
            self.item = self.pool.get_item(item_id)

            for song in self.item.songs:
                self.song = song
                realfilename = os.path.join('/tmp/kakrafoon',str(self.item.key), str(song.key))
                print(realfilename)
                self.player = kakraplay.get_player(realfilename,
                                                   subtune=song.subtune,
                                                   loops=song.loops)
                wait_for_all([self.running])
                self.player.play()
                self.player = None
                if self.skip_current_item:
                    break
            self.pool.remove_item(item_id)
            self.skip_current_item = False
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

    def skip_item(self):
        if self.item:
            self.skip_current_item = True
            if self.player:
                self.player.abort()
