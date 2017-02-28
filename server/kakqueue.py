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

def synchronised(f):
    """Synchronisation decorator"""

    def real_function(*args, **kw):
        args[0].lock.acquire()
        try:
            return f(*args, **kw)
        finally:
            args[0].lock.release()
    return real_function


class _QueueItem(object):
    def __init__(self, obj, user, songs, length=None):
        self.obj = obj
        self.user = user
        self.songs = songs

    def __repr__(self):
        return "<_Queue_item obj: %s, user: %s, songs: %d>"%(self.obj, self.user, self.songs)


class Queue(object):
    def __init__(self):
        self.user_order = []
        self.user_queue = {}
        self.user_skip = {}
        self.nonempty = threading.Event()
        self.lock = threading.Lock()
        self.obj_item = {}

    def _purge_user(self, user):
        """Remove all traces of a user from the queue"""
        self.user_order.remove(user)
        del self.user_queue[user]
        del self.user_skip[user]

    @synchronised
    def enqueue(self, obj, user, songs, length=None):
        """Add an item to the queue"""

        item = _QueueItem(obj, user, songs, length)
        if not user in self.user_order:
            self.user_order.append(user)
            self.user_queue[user] = []
            self.user_skip[user] = 0
        self.user_queue[user].append(item)
        self.obj_item[obj] = item
        self.nonempty.set()

    @synchronised
    def get_first(self):
        """Return the first item in the queue, or None if the queue is empty"""
        for u in self.user_order:
            if self.user_skip[u] == 0:
                return self.user_queue[u][0].obj
        return None

    @synchronised
    def get_all(self):
        """Get all queue items, in the correct order"""
        order = self.user_order.copy()
        position = dict([(u, 0) for u in order])
        skip = self.user_skip.copy()
        queue = []

        while order:
            remove = set()
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
                        remove.add(x)

            for x in remove:
                order.remove(x)
        return queue

    @synchronised
    def dequeue(self, obj):
        """Remove an item from the queue

        The next item in the affected user's queue will take its place.
        """
        try:
            item = self.obj_item.pop(obj)
            self.user_queue[item.user].remove(item)
            r = True
            if self.user_skip[item.user] == 0 and not self.user_queue[item.user]:
                self._purge_user(item.user)
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

    @synchronised
    def pop(self):
        """Pop the first item from the queue

        Note that this is different from dequeue() as pop() will retain the global
        order of items. Use pop() when removing the item that was just played.
        """
        for x in self.user_order:
            if self.user_skip[x] > 0:
                continue
            item = self.user_queue[x].pop(0)
            self.obj_item.pop(item.obj)
            self.user_skip[x] = item.songs
            break
        self._normalise()
        return item.obj if item else None


def _make_queue():
    q = Queue()
    q.enqueue('Ax1', 'A', 1, None)
    q.enqueue('Ay1', 'A', 1, None)
    q.enqueue('Az2', 'A', 2, None)
    q.enqueue('Bx3', 'B', 3, None)
    q.enqueue('By1', 'B', 1, None)
    q.enqueue('Cx2', 'C', 2, None)
    q.enqueue('Cy2', 'C', 2, None)
    return q


class QueueTest(unittest.TestCase):
    def test_basic(self):
        q = _make_queue()
        o = q.get_all()
        self.assertEqual(o, ['Ax1','Bx3','Cx2','Ay1','Az2','Cy2','By1'])

    def test_pop(self):
        q = _make_queue()
        order = ['Ax1','Bx3','Cx2','Ay1','Az2','Cy2','By1']
        while order:
            self.assertEqual(q.get_all(), order)
            self.assertEqual(q.get_first(), order[0])
            qi = q.pop()
            oi = order.pop(0)
            self.assertEqual(qi, oi)
        self.assertEqual(q.user_order, [])
        self.assertEqual(q.user_skip, {})
        self.assertEqual(q.user_queue, {})

    def test_dequeue(self):
        q = _make_queue()
        q.dequeue('Ax1')
        self.assertEqual(q.get_all(), ['Ay1','Bx3','Cx2','Az2','Cy2','By1'])
        q.dequeue('Bx3')
        self.assertEqual(q.get_all(), ['Ay1','By1','Cx2','Az2','Cy2'])

if __name__ == '__main__':
    unittest.main()
