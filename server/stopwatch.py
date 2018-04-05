import time
import unittest

class StopWatch(object):
    def __init__(self):
        self.start_time = None
        self.pause_time = None
        
    def start(self):
        self.start_time = time.time()

    def pause(self):
        if self.pause_time is None:
            self.pause_time = time.time()

    def resume(self):
        now = time.time()
        self.start_time += now - self.pause_time
        self.pause_time = None

    def read(self):
        if self.pause_time:
            return self.pause_time - self.start_time
        else:
            return time.time() - self.start_time


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
        self.assertGreater(t, 0.19)
        self.assertLess(t, 0.21)

if __name__ == '__main__':
    unittest.main()
