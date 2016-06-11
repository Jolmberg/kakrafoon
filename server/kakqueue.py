import threading
import unittest

# A queue is an ordered collection of items.
# Each item has the following properties:
# obj - reference to the real queue item
# user - the user who queued this item
# songs - the number of songs in this item
# length - total length of all songs in the item (if known)

# This queue implementation schedules items as fairly as possible, based only
# on the number of songs in each item. The length parameter is not used.

# TODO: This isn't thread safe. Does it need to be?

class _QueueItem(object):
    def __init__(self, obj, user, songs, length=None):
        self.obj = obj
        self.user = user
        self.songs = songs


class Queue(object):
    def __init__(self):
        self.user_order = []
        self.user_queue = {}
        self.user_skip = {}
        self.nonempty = threading.Event()

    def _purge_user(self, user):
        """Remove all traces of a user from the queue"""
        self.user_order.remove(user)
        del self.user_queue[user]
        del self.user_skip[user]

    def enqueue(self, obj, user, songs, length=None):
        """Add an item to the queue"""
        item = _QueueItem(obj, user, songs, length)
        if not user in self.user_order:
            self.user_order.append(user)
            self.user_queue[user] = []
            self.user_skip[user] = 0
        self.user_queue[user].append(item)
        self.nonempty.set()

    def get_first(self):
        """Return the first item in the queue, or None if the queue is empty"""
        for u in self.user_order:
            if self.user_skip[u] == 0:
                return self.user_queue[u][0].obj
        return None

    def get_all(self):
        """Get all queue items, in the correct order"""
        order = self.user_order[:]
        position = dict([(u, 0) for u in order])
        skip = self.user_skip.copy()
        queue = []
        remove = None
        while order:
            for x in order:
                if skip[x] > 0:
                    skip[x] -= 1
                else:
                    if len(self.user_queue[x]) > position[x]:
                        item = self.user_queue[x][position[x]]
                        position[x] += 1
                        skip[x] = item.songs - 1
                        queue.append(item.obj)
                    else:
                        remove = x

            if remove:
                order.remove(x)
                remove = None
        return queue

    def dequeue(self, user, obj):
        """Remove an item from the queue

        The next item in the affected user's queue will take its place.
        """
        try:
            self.user_queue[user].remove(obj)
            r = True
            if self.user_skip[user] == 0 and not self.user_queue[user]:
                self._purge_user(user)
                self._normalise()
        except:
            r = False
        return r

    def _normalise(self):
        """Normalise skip data and clean out worthless users"""
        m = min(self.user_skip.values())
        for x in [k for k in self.user_skip]:
            self.user_skip[x] -= m
            if self.user_skip[x] == 0 and not self.user_queue[x]:
                self._purge_user(x)
        if not self.user_order:
            self.nonempty.clear()

    def pop(self):
        """Pop the first item from the queue

        Note that this is different from dequeue() as pop() will retain the global
        order of items. Use pop() when retrieving the next item to play.
        """
        for x in self.user_order:
            if self.user_skip[x] > 0:
                continue
            item = self.user_queue[x].pop(0)
            self.user_skip[x] = item.songs
            break
        self._normalise()
        return item.obj if item else None


def _make_queue():
    q = Queue()
    q.enqueue('A1', 'A', 1, None)
    q.enqueue('A1', 'A', 1, None)
    q.enqueue('A2', 'A', 2, None)
    q.enqueue('B3', 'B', 3, None)
    q.enqueue('B1', 'B', 1, None)
    q.enqueue('C2', 'C', 2, None)
    q.enqueue('C2', 'C', 2, None)
    return q


class QueueTest(unittest.TestCase):
    def test1(self):
        q = _make_queue()
        o = q.get_all()
        self.assertEqual(o, ['A1','B3','C2','A1','A2','C2','B1'])

    def test2(self):
        q = _make_queue()
        order = ['A1','B3','C2','A1','A2','C2','B1']
        while order:
            self.assertEqual(q.get_all(), order)
            self.assertEqual(q.get_first(), order[0])
            qi = q.pop()
            oi = order.pop(0)
            self.assertEqual(qi, oi)
        self.assertEqual(q.user_order, [])
        self.assertEqual(q.user_skip, {})
        self.assertEqual(q.user_queue, {})


if __name__ == '__main__':
    unittest.main()
