import shutil
import os

def save_song(item_id, song_id, fileobj):
    path = os.path.join('/tmp/kakrafoon', str(item_id))
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, str(song_id))
    fileobj.save(filepath)


def save_songs(item):
    for song in item.songs:
        save_song(item.key, song.key, song.file_object)
        del song.file_object
        

class SongPool(object):

    def __init__(self):
        self.items = {}
        self.id_counter = 1

    def add_item(self, item):
        item_id = self.id_counter
        item.key = item_id
        save_songs(item)
        self.id_counter += 1
        self.items[item_id] = item
        return item_id
        
    def get_item(self, item_id):
        return self.items[item_id]

    def remove_item(self, item_id):
        if item_id in self.items:
            shutil.rmtree(os.path.join('/tmp/kakrafoon', str(item_id)))
            del self.items[item_id]
            return True
        else:
            return False
            
