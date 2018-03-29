import configparser
import os

_configfiles = ['/etc/kakrafoond.conf', 'kakrafoond.conf']

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

