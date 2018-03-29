import alsaaudio
from config import dictionary as config

_real_mixers = alsaaudio.mixers()
allowed_mixers = [x for x in config['allowed_mixers'].split(',') if x in _real_mixers]
default_mixer = config['default_mixer'] if config['default_mixer'] in allowed_mixers else None

channel_names = ['front-left','front-right']

class NoSuchControlError(Exception):
    pass

class NoSuchChannelError(Exception):
    pass

def get_all():
    controls = {}
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
        controls[name] = channels
    return controls

def set(volume, channel=None, control=None):
    mixer = None
    if control:
        if control in allowed_mixers:
            mixer = alsaaudio.Mixer(control)
    else:
        if default_mixer:
            mixer = alsaaudio.Mixer(default_mixer)

    if not mixer:
        raise NoSuchControlError()

    if channel:
        if channel not in channel_names:
            raise NoSuchChannelError()
        mixer.setvolume(volume, channel_names.index(channel))
    else:
        mixer.setvolume(volume)
