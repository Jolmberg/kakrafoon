import time
import unittest

class StopWatch(object):
    def __init__(self):
        self.reset()
        
    def start(self):
        self.start_time = time.time()

    def pause(self):
        if self.pause_time is None:
            self.pause_time = time.time()

    def resume(self):
        if self.pause_time:
            self.total_pause_time += time.time() - self.pause_time
            self.pause_time = None

    def read(self):
        if not self.start_time:
            return 0
        elif self.pause_time:
            return self.pause_time - self.start_time - self.total_pause_time
        else:
            return time.time() - self.start_time - self.total_pause_time

    def reset(self):
        self.start_time = None
        self.pause_time = None
        self.total_pause_time = 0


class StopWatchTest(unittest.TestCase):
    def test_basic(self):
        w = StopWatch()
        w.start()
        time.sleep(0.1)
        w.pause()
        time.sleep(0.2)
        w.resume()
        time.sleep(0.1)
        t = w.read()
        w.pause()
        self.assertGreater(t, 0.18)
        self.assertLess(t, 0.22)
        t2 = w.read()
        self.assertGreater(t2, t)
        self.assertGreater(t2, 0.18)
        self.assertLess(t2, 0.22)
        time.sleep(0.1)
        t3 = w.read()
        self.assertEqual(t2, t3)

if __name__ == '__main__':
    unittest.main()
