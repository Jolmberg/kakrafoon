import threading
import os

import kakraplay


class Control(threading.Thread):

    def __init__(self, kpool, kqueue):
        self.pool = kpool
        self.queue = kqueue
        self.running = False
        self.item = None
        self.song_id = 0
        self.player = None
        self.paused = False
        super(Control, self).__init__()

    def run(self):
        self.running = True
        while self.running:
            item_id = None
            while self.running and item_id is None:
                self.queue.nonempty.wait(1)
                item_id = self.queue.get_first()
            self.item = self.pool.get_item(item_id)

            for song in self.item.songs:
                realfilename = os.path.join('/tmp/kakrafoon',str(self.item.key), str(song.key))
                print(realfilename)
                self.player = kakraplay.get_player(realfilename)
                self.player.play()
            self.queue.pop()
