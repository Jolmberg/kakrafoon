import sqlite3
import threading
from config import dictionary as config
from contextlib import closing

CREATE = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, plays INTEGER, playtime INTEGER)",
    "CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, songname TEXT, hash TEXT, subtune INTEGER, length INTEGER, looplength INTEGER, plays INTEGER, playtime INTEGER, UNIQUE(hash, subtune))",
    "CREATE TABLE IF NOT EXISTS log (id INTEGER PRIMARY KEY, userid INTEGER REFERENCES users(id), songid INTEGER REFERENCES songs(id), timestamp INTEGER, duration INTEGER)",
    "CREATE TABLE IF NOT EXISTS usersongs (id INTEGER PRIMARY KEY, userid INTEGER REFERENCES users(id), songid INTEGER REFERENCES songs(id), plays INTEGER, playtime INTEGER)",
    "CREATE TABLE IF NOT EXISTS loops (songid INTEGER PRIMARY KEY REFERENCES songs(id), loops INTEGER, length INTEGER)",
    "CREATE TABLE IF NOT EXISTS playing (id INTEGER PRIMARY KEY, username TEXT, songname TEXT, starttime INTEGER, hash TEXT)",
    "CREATE INDEX IF NOT EXISTS log_userid ON log(userid)",
    "CREATE INDEX IF NOT EXISTS log_songid ON log(songid)",
    "CREATE INDEX IF NOT EXISTS users_username ON users(username)",
    "CREATE INDEX IF NOT EXISTS songs_hash ON songs(hash)",
    "CREATE INDEX IF NOT EXISTS songs_songname ON songs(songname)",
    "CREATE INDEX IF NOT EXISTS usersongs_userid ON usersongs(userid)",
    "CREATE INDEX IF NOT EXISTS usersongs_songid ON usersongs(songid)",
    "CREATE INDEX IF NOT EXISTS loops_ssongid ON loops(songid)",
    ]

class Stats(object):
    def __init__(self):
        self.dbfile = config['stats_database']
        self._user_cache = {}
        self._song_cache = {}
        self._usersong_cache = {}
        self._connections = {}
        self.create()

    def create(self):
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            for c in CREATE:
                cur.execute(c)
        con.commit()

    def get_connection(self):
        thread_id = threading.get_ident()
        if thread_id in self._connections:
            return self._connections[thread_id]
        connection = sqlite3.connect(self.dbfile)
        self._connections[thread_id] = connection
        return connection

    def add_user(self, name):
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('insert into users (username, plays, playtime) values (?,?,?)',
                            (name, 0, 0))
                userid = cur.lastrowid
            except Exception as e:
                raise e
        con.commit()
        self._user_cache[name] = userid
        return userid

    def get_user(self, name):
        if name in self._user_cache:
            return self._user_cache[name]

        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('select id from users where username=?', (name,))
                r = cur.fetchall()
                if len(r) == 0:
                    return None
                self._user_cache[name] = r[0][0]
                return r[0][0]
            except Exception as e:
                raise e

    def get_or_add_user(self, name):
        userid = self.get_user(name)
        if userid is not None:
            return userid
        return self.add_user(name)

    def add_song(self, name, songhash, subtune=None, length=None, loops=None):
        if subtune is None:
            subtune = -1
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                columns = ['songname', 'hash', 'subtune', 'plays', 'playtime']
                values = [name, songhash, subtune, 0, 0]
                if length is not None and (loops is None or loops == 1):
                    columns.append('length')
                    values.append(length)
                cur.execute('insert into songs (%s) values (%s)' %
                            (','.join(columns), ','.join(['?'] * len(values))),
                            tuple(values))
                songid = cur.lastrowid

                if loops is not None and length is not None:
                    cur.execute('insert into loops(songid, loops, length) values(?,?,?)',
                                (songid, loops, length))
            except Exception as e:
                raise e
        con.commit()
        self._song_cache[(songhash, subtune)] = (songid, name, length, None)
        return songid

    def get_song_by_id(self, songid):
        con = self.get_connection()
        with(closing(con.cursor())) as cur:
             try:
                 cur.execute('select id, songname, subtune, length, looplength, plays, playtime from songs where id=?', (songid,))
                 r = cur.fetchall()
                 if len(r) == 0:
                     return None
                 return (r[0][0], r[0][1], r[0][2], r[0][3], r[0][4], r[0][5], r[0][6])
             except Exception as e:
                 raise e

    def get_user_by_id(self, userid):
        con = self.get_connection()
        with(closing(con.cursor())) as cur:
             try:
                 cur.execute('select id, username, plays, playtime from users where id=?', (userid,))
                 r = cur.fetchall()
                 if len(r) == 0:
                     return None
                 return (r[0][0], r[0][1], r[0][2], r[0][3])
             except Exception as e:
                 raise e

    def get_song(self, songhash, subtune=None):
        if subtune is None:
            subtune = -1
        if (songhash, subtune) in self._song_cache:
            print("Song is cached: " + str(self._song_cache[(songhash, subtune)]))
            return self._song_cache[(songhash, subtune)]
        # TODO: Should the song cache size be limited somehow?
        print("Song is not cached: " + str((songhash, subtune)))
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('select id, songname, length, looplength from songs where hash=? and subtune=?',
                            (songhash, subtune))
                r = cur.fetchall()
                if len(r) == 0:
                    return None
                result = (r[0][0], r[0][1], r[0][2], r[0][3])
                self._song_cache[(songhash, subtune)] = result
                return result
            except Exception as e:
                raise e

    def get_or_add_song(self, name, songhash, subtune=None, length=None, loops=None):
        song = self.get_song(songhash, subtune)
        if song is not None:
            if song[3] is None and loops is not None:
                self._calculate_loops(song[0], loops, length)
            return song[0]
        return self.add_song(name, songhash, subtune, length, loops)

    def _calculate_loops(self, songid, loops, length):
        con = self.get_connection()
        commit = False
        with closing(con.cursor()) as cur:
            try:
                cur.execute('select loops, length from loops where songid=?', (songid,))
                r = cur.fetchall()
                if len(r) > 0:
                    loops2 = r[0][0]
                    if loops2 != loops:
                        length2 = r[0][1]
                        lengthdiff = length - length2
                        loopdiff = loops - loops2
                        looplength = lengthdiff / loopdiff
                        reallength = length - looplength*(loops-1)
                        if looplength >= 0 and reallength >= -5:
                            if reallength < 0:
                                # Allow for minor inaccuracy
                                reallength = 0
                            cur.execute('update songs set length=?, looplength=? where id=?',
                                        (round(reallength), round(looplength), songid))
                        # Always discard previous loop data. If it was used, we won't need it again,
                        # and if it produced a bad looplength it is not reliable anyway.
                        cur.execute('delete from loops where songid=?', (songid,))
                        commit = True
            except Exception as e:
                raise e
        if commit:
            con.commit()

    def get_usersong(self, userid, songid):
        if (userid, songid) in self._usersong_cache:
            return self._usersong_cache[(userid, songid)]

        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('select id from usersongs where userid=? and songid=?', (userid, songid))
                r = cur.fetchall()
                if len(r) == 0:
                    return None
                self._usersong_cache[(userid, songid)] = r[0][0]
                return r[0][0]
            except Exception as e:
                raise e

    def log_song(self, username, songname, songhash, subtune, loops, starttime, duration, aborted):
        starttime = round(starttime)
        duration = round(duration)
        length = None if aborted else duration
        if aborted:
            loops = None
        userid = self.get_or_add_user(username)
        songid = self.get_or_add_song(songname, songhash, subtune, length, loops)
        usersongid = self.get_usersong(userid, songid)
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('insert into log (userid, songid, timestamp, duration) values(?,?,?,?)',
                            (userid, songid, starttime, duration))
                cur.execute('update songs set plays=plays+1, playtime=playtime+? where id=?',
                            (duration, songid))
                cur.execute('update users set plays=plays+1, playtime=playtime+? where id=?',
                            (duration, userid))
                if usersongid is None:
                    cur.execute('insert into usersongs (userid, songid, plays, playtime) values(?,?,?,?)',
                                (userid, songid, 1, duration))
                else:
                    cur.execute('update usersongs set plays=plays+1, playtime=playtime+? where userid=? and songid=?',
                            (duration, userid, songid))
            except Exception as e:
                raise e
        con.commit()
