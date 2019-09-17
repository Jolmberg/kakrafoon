Hacking on kakrafoon(d)
=======================

## Test environment

The following python packages are needed:
flask, marshmallow, werkzeug, alsaaudio, requests

If alsaaudio (called pyalsaaudio in pip) is not available on your platform,
you can add a fake alsaaudio.py file to your server directory with the
following content:

    def mixers():
        return ['Master', 'PCM']

This way you can still run kakrafoond, but mixer functions will of course not
be available.

Start the server by running kakrafoond.py in the server directory.

## How kakqueue.py works

Each user has their own separate queue. A queue is a list of queue items, where
each item is in itself a list of songs. This makes enqueueing and dequeueing
trivial as each operation only affects a single list.

Assume user A has queued up three items, containing the songs a1, a2, and a3
respectively. User B has queued up a single item containing the three songs
b1, b2, and b3. User C has queued up one item containing the songs c1 and c2,
and a second item containing the song c3.

Placing the queues side by side they would look like this:

         A      B      C
       +----+ +----+ +----+
    1  | a1 | | b1 | | c1 |
       +----+ |    | |    |
       +----+ |    | |    |
    2  | a2 | | b2 | | c2 |
       +----+ |    | +----+
       +----+ |    | +----+
    3  | a3 | | b3 | | c3 |
       +----+ +----+ +----+

The internal ordering of these three queues is decided on a first-come
first-served basis, in this case user A was the first to queue up an item and
user B was next. Beyond that, the order in which the items were enqueued is
irrelevant.

The global queue order is calculated on the fly by traversing the image above
line by line, reading each line from left to right, and adding each queue item
found to the global queue. Line one yields the items [a1], [b1 b2 b3], and
[c1 c2]. Line two yields the item [a2]. (Although the songs b2 and c2 are
located on line two they are parts of items belonging to line 1 and are of
course not added a second time.) Finally, line three yields [a3] and [c3], for
a global queue of [a1], [b1 b2 b3], [c1 c2], [a2], [a3], [c3].
