import shutil
import os

def _save_song(item_id, song_id, fileobj):
    path = os.path.join('/tmp/kakrafoon', str(item_id))
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, str(song_id))
    fileobj.save(filepath)


def _save_songs(item):
    for song in item.songs:
        _save_song(item.key, song.key, song.file_object)
        del song.file_object
        

class SongPool(object):
    """The SongPool stores and keeps track of items that have been uploaded"""
    def __init__(self):
        self.items = {}
        self.id_counter = 1

    def add_item(self, item):
        """Adds an item to the pool, saves its files to the file system and
        assigns an id to it.
        """
        item_id = self.id_counter
        item.key = item_id
        _save_songs(item)
        self.id_counter += 1
        self.items[item_id] = item
        return item_id
        
    def get_item(self, item_id):
        """Retrieves an item based on an id"""
        return self.items[item_id]

    def remove_item(self, item_id):
        """Removes an item and deletes its files"""
        if item_id in self.items:
            shutil.rmtree(os.path.join('/tmp/kakrafoon', str(item_id)))
            del self.items[item_id]
            return True
        else:
            return False
