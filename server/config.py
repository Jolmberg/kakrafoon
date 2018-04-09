import configparser
import os

class ConfigError(Exception):
    pass

_configfiles = ['/etc/kakrafoond.conf', 'kakrafoond.conf']
_required = ["allowed_mixers", "default_mixer", "song_pool_path"]

cfg = configparser.ConfigParser()
used_config = None

for cf in _configfiles:
    try:
        with open(cf, 'r') as f:
            r = cfg.read_file(f)
            used_config = cf
            break
    except:
        pass

dictionary = {}
if cfg.has_section('kakrafoond'):
    dictionary = dict(cfg.items('kakrafoond'))

for key in _required:
    if not key in dictionary:
        raise ConfigError("Missing configuration: " + key)
