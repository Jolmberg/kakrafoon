import sqlite3
import threading
from config import dictionary as config
from contextlib import closing

CREATE = [
    "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, plays INTEGER, playtime INTEGER, skips INTEGER)",
    "CREATE TABLE IF NOT EXISTS songs (id INTEGER PRIMARY KEY, songname TEXT, hash TEXT, subtune INTEGER, length INTEGER, looplength INTEGER, plays INTEGER, playtime INTEGER, skips INTEGER, UNIQUE(hash, subtune))",
    "CREATE TABLE IF NOT EXISTS log (id INTEGER PRIMARY KEY, userid INTEGER REFERENCES users(id), songid INTEGER REFERENCES songs(id), timestamp INTEGER, duration INTEGER, skipped INTEGER)",
    "CREATE TABLE IF NOT EXISTS usersongs (id INTEGER PRIMARY KEY, userid INTEGER REFERENCES users(id), songid INTEGER REFERENCES songs(id), plays INTEGER, playtime INTEGER, skips INTEGER)",
    "CREATE TABLE IF NOT EXISTS loops (songid INTEGER PRIMARY KEY REFERENCES songs(id), loops INTEGER, length INTEGER)",
    "CREATE TABLE IF NOT EXISTS playing (id INTEGER PRIMARY KEY, username TEXT, songname TEXT, starttime INTEGER, hash TEXT)",
    "CREATE TABLE IF NOT EXISTS kakrafoon (id INTEGER PRIMARY KEY, key TEXT, value TEXT)",
    "CREATE INDEX IF NOT EXISTS log_userid ON log(userid)",
    "CREATE INDEX IF NOT EXISTS log_songid ON log(songid)",
    "CREATE INDEX IF NOT EXISTS users_username ON users(username)",
    "CREATE INDEX IF NOT EXISTS users_plays ON users(plays)",
    "CREATE INDEX IF NOT EXISTS users_playtime ON users(playtime)",
    "CREATE INDEX IF NOT EXISTS users_skips ON users(skips)",
    "CREATE INDEX IF NOT EXISTS songs_hash ON songs(hash)",
    "CREATE INDEX IF NOT EXISTS songs_songname ON songs(songname)",
    "CREATE INDEX IF NOT EXISTS songs_plays ON songs(plays)",
    "CREATE INDEX IF NOT EXISTS songs_playtime ON songs(playtime)",
    "CREATE INDEX IF NOT EXISTS songs_skips ON songs(skips)",
    "CREATE INDEX IF NOT EXISTS usersongs_userid ON usersongs(userid)",
    "CREATE INDEX IF NOT EXISTS usersongs_songid ON usersongs(songid)",
    "CREATE INDEX IF NOT EXISTS usersongs_plays ON usersongs(plays)",
    "CREATE INDEX IF NOT EXISTS usersongs_playtime ON usersongs(playtime)",
    "CREATE INDEX IF NOT EXISTS usersongs_skips ON usersongs(skips)",
    "CREATE INDEX IF NOT EXISTS loops_ssongid ON loops(songid)",
    ]

VERSION = 1

class StatsError(Exception):
    pass

class Stats(object):
    def __init__(self):
        self.dbfile = config['stats_database']
        self._user_cache = {}
        self._song_cache = {}
        self._usersong_cache = {}
        self._connections = {}
        self.create()

    def create(self):
        version = None
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            cur.execute("select * from sqlite_master where type='table' and name='kakrafoon'")
            r = cur.fetchall()
            if len(r) != 1:
                for c in CREATE:
                    cur.execute(c)
                    #con.commit()
                cur.execute("insert into kakrafoon(key, value) values('version', ?)",
                                (str(VERSION),))
                version = VERSION
            else:
                cur.execute("select value from kakrafoon where key='version'")
                r = cur.fetchall()
                version = int(r[0][0])
        con.commit()

        if version < VERSION:
            self.upgrade(version)
        elif version > VERSION:
            raise StatsError('Database version (%d) is from the future' % (version,))

    def upgrade(self, from_version):
        # Add code to upgrade the any older database schema to the current version here
        raise StatsError('Cannot upgrade from this database version (%d)' % (from_version,))

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
                cur.execute('insert into users(username, plays, playtime, skips) values(?,?,?,?)',
                            (name, 0, 0, 0))
                userid = cur.lastrowid
            except Exception as e:
                raise e
        con.commit()
        self._user_cache[name] = userid
        return userid

    def fetch_all(self, query, params=(), cur=None):
        if not cur:
            con = self.get_connection()
            con.row_factory = sqlite3.Row
            with closing(con.cursor()) as cur:
                cur.execute(query, params)
                return cur.fetchall()
        else:
            cur.execute(query, params)
            return cur.fetchall()

    def get_user_by_name(self, name):
        if name in self._user_cache:
            return self._user_cache[name]

        r = self.fetch_all('select id from users where username=?', (name,))
        if len(r) == 0:
            return None
        self._user_cache[name] = r[0][0]
        return r[0][0]

    def get_or_add_user(self, name):
        userid = self.get_user_by_name(name)
        if userid is not None:
            return userid
        return self.add_user(name)

    def add_song(self, name, songhash, subtune=None, length=None, loops=None):
        if subtune is None:
            subtune = -1
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                columns = ['songname', 'hash', 'subtune', 'plays', 'playtime', 'skips']
                values = [name, songhash, subtune, 0, 0, 0]
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

    def get_song_by_column(self, column, value):
        r = self.fetch_all('select id, songname, subtune, length, looplength, plays, playtime, skips from songs where %s=?' % (column,), (value,))
        if len(r) == 0:
            return None
        return (r[0][0], r[0][1], r[0][2], r[0][3], r[0][4], r[0][5], r[0][6], r[0][7])

    def get_user_by_column(self, column, value):
        r = self.fetch_all('select id, username, plays, playtime, skips from users where %s=?' % (column,), (value,))
        if len(r) == 0:
            return None
        return (r[0][0], r[0][1], r[0][2], r[0][3], r[0][4])

    def get_song_by_hash_and_subtune(self, songhash, subtune=None):
        if subtune is None:
            subtune = -1
        if (songhash, subtune) in self._song_cache:
            return self._song_cache[(songhash, subtune)]
        # TODO: Should the song cache size be limited somehow?
        con = self.get_connection()
        r = self.fetch_all('select id, songname, length, looplength from songs where hash=? and subtune=?',
                            (songhash, subtune))
        if len(r) == 0:
            return None
        result = (r[0][0], r[0][1], r[0][2], r[0][3])
        self._song_cache[(songhash, subtune)] = result
        return result

    def get_or_add_song(self, name, songhash, subtune=None, length=None, loops=None):
        song = self.get_song_by_hash_and_subtune(songhash, subtune)
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

        r = self.fetch_all('select id from usersongs where userid=? and songid=?', (userid, songid))
        if len(r) == 0:
            return None
        self._usersong_cache[(userid, songid)] = r[0][0]
        return r[0][0]

    def log_song(self, username, songname, songhash, subtune, loops, starttime, duration, aborted):
        starttime = round(starttime)
        duration = round(duration)
        length = None if aborted else duration
        skipstr = ''
        if aborted:
            loops = None
            skipstr = ', skips=skips+1 '
        userid = self.get_or_add_user(username)
        songid = self.get_or_add_song(songname, songhash, subtune, length, loops)
        usersongid = self.get_usersong(userid, songid)
        con = self.get_connection()
        with closing(con.cursor()) as cur:
            try:
                cur.execute('insert into log (userid, songid, timestamp, duration) values(?,?,?,?)',
                            (userid, songid, starttime, duration))
                cur.execute('update songs set plays=plays+1, playtime=playtime+?%s where id=?' % (skipstr,),
                            (duration, songid))
                cur.execute('update users set plays=plays+1, playtime=playtime+?%s where id=?' % (skipstr,),
                            (duration, userid))
                if usersongid is None:
                    cur.execute('insert into usersongs (userid, songid, plays, playtime, skips) values(?,?,?,?,?)',
                                (userid, songid, 1, duration, 1 if aborted else 0))
                else:
                    cur.execute('update usersongs set plays=plays+1, playtime=playtime+?%s where userid=? and songid=?' % (skipstr,),
                                (duration, userid, songid))
            except Exception as e:
                raise e
        con.commit()

    def metric_thing_by_value(self, thing, value, limit=10, offset=0, ascending=False):
        return self.fetch_all('select id as {0}id, {0}name, {1} from {0}s order by {1} {2} limit ? offset ?'.format(thing, value, 'asc' if ascending else 'desc'), (limit, offset))

    def metric_usersongs_thing_by_value(self, thing, value, id, limit=10, offset=0, ascending=False):
        idthing = 'song' if thing == 'user' else 'user'
        return self.fetch_all('select i.id as {0}id, i.{0}name, us.{2} from usersongs us inner join {0}s i on us.{0}id = i.id where us.{1}id=? order by us.{2} {3} limit ? offset ?'.format(thing, idthing, value, 'asc' if ascending else 'desc'), (id, limit, offset))

    def metric_usersongs_thing_by_unique_value(self, thing, number, limit=10, offset=0, ascending=False):
        return self.fetch_all('select i.id as {0}id, i.{0}name, count(*) as {1} from usersongs us inner join {0}s i on us.{0}id = i.id group by 1,2 order by 3 {2} limit ? offset ?'.format(thing, number, 'asc' if ascending else 'desc'), (limit, offset))
