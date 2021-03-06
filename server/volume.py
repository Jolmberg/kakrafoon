import alsaaudio
from collections import OrderedDict
from config import dictionary as config

_real_mixers = alsaaudio.mixers()
allowed_mixers = [x for x in config['allowed_mixers'].split(',') if x in _real_mixers]
default_mixer = config['default_mixer'] if config['default_mixer'] in allowed_mixers else None

# The default mixer should always be the first one in the list
if default_mixer and default_mixer in allowed_mixers and allowed_mixers[0] != default_mixer:
    allowed_mixers.remove(default_mixer)
    allowed_mixers.insert(0, default_mixer)

channel_names = ['front-left','front-right']

class NoSuchMixerError(Exception):
    pass

class NoSuchChannelError(Exception):
    pass

def get_all():
    mixers = OrderedDict()
    for name in allowed_mixers:
        try:
            m = alsaaudio.Mixer(name)
        except alsaaudio.ALSAAudioError as e:
            continue
        channels={}
        v = m.getvolume()
        if len(v) == 0:
            continue
        elif len(v) == 1:
            channels={"mono":v[0]}
        else:
            channels=dict(zip(channel_names, v))
        mixers[name] = channels
    return mixers

def set(volume, channel=None, mixer=None):
    mixer = None
    if mixer:
        if mixer in allowed_mixers:
            mixer = alsaaudio.Mixer(mixer)
    else:
        if default_mixer:
            mixer = alsaaudio.Mixer(default_mixer)

    if not mixer:
        raise NoSuchMixerError()

    if channel:
        if channel not in channel_names:
            raise NoSuchChannelError()
        mixer.setvolume(volume, channel_names.index(channel))
    else:
        mixer.setvolume(volume)
