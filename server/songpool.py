import hashlib
import shutil
import os
from config import dictionary as config

os.makedirs(config['song_pool_path'], exist_ok=True)

def _save_and_hash_song(item_id, song_id, fileobj):
    path = os.path.join(config['song_pool_path'], str(item_id))
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join(path, str(song_id))
    fileobj.save(filepath)
    hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for x in iter(lambda: f.read(4096), b""):
            hash.update(x)
    return hash.hexdigest()


def _save_and_hash_songs(item):
    for song in item.songs:
        hash = _save_and_hash_song(item.key, song.key, song.file_object)
        del song.file_object
        song.hash = hash
        

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
        _save_and_hash_songs(item)
        self.id_counter += 1
        self.items[item_id] = item
        return item_id
        
    def get_item(self, item_id):
        """Retrieves an item based on an id"""
        return self.items[item_id]

    def remove_item(self, item_id):
        """Removes an item and deletes its files"""
        if item_id in self.items:
            shutil.rmtree(os.path.join(config['song_pool_path'], str(item_id)))
            del self.items[item_id]
            return True
        else:
            return False

    def remove_song(self, item_id, song_id):
        """Removes a song from an item and deletes its file"""
        if not item_id in self.items:
            print("Item not found")
            return False
        item = self.items[item_id]
        song = None
        for s in item.songs:
            print("key: " + str(s.key))
            if s.key == song_id:
                song = s
                break
        else:
            print("Song not found")
            return False
        print(song)
        item.songs.remove(song)
        os.remove(os.path.join(config['song_pool_path'], str(item_id), str(song_id)))
        return True
