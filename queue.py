import unittest

# A queue is an ordered collection of items.
# Each item has the following properties:
# obj - reference to the real queue item
# user - the user who queued this item
# songs - the number of songs in this item
# length - total length of all songs in the item (if known)

# This queue implementation schedules items as fairly as possible, based only
# on the number of songs in each item. The length parameter is not used.

class _QueueItem(object):
    def __init__(self, obj, user, songs, length):
        self.obj = obj
        self.user = user
        self.songs = songs


class Queue(object):
    def __init__(self):
        self.user_order = []
        self.user_queue = {}
        self.user_skip = {}

    def add(self, obj, user, songs, length):
        """Add an item to the queue"""
        item = _QueueItem(obj, user, songs, length)
        if not user in self.user_order:
            self.user_order.append(user)
            self.user_queue[user] = []
            self.user_skip[user] = 0
        self.user_queue[user].append(item)

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

    def remove(self, user, obj):
        """Remove an item from the queue

        The next item in the affected user's queue will take its place.
        """
        try:
            self.user_queue[user].remove(obj)
        except:
            return False
        if not self.user_queue[user]:
            self.user_order.remove(user)

    def _normalise_skip(self):
        # TODO: Normalise everything.
        m = min(self.user_skip.values())
        for x in self.user_skip:
            self.user_skip[x] -= m

    def pop(self):
        """Pop the first item from the queue

        Note that this is different from remove() as pop() will retain the global
        order of items. Use pop() when retrieving the next item to play.
        """
        for x in self.user_order:
            if self.user_skip[x] > 0:
                continue
            item = self.user_queue[x].pop(0)
            self.user_skip[x] = item.songs
            break
        self._normalise_skip()
        return item.obj


def _make_queue():
    q = Queue()
    q.add('A1', 'A', 1, None)
    q.add('A1', 'A', 1, None)
    q.add('A2', 'A', 2, None)
    q.add('B3', 'B', 3, None)
    q.add('B1', 'B', 1, None)
    q.add('C2', 'C', 2, None)
    q.add('C2', 'C', 2, None)
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
            qi = q.pop()
            oi = order.pop(0)
            self.assertEqual(qi, oi)


if __name__ == '__main__':
    unittest.main()
