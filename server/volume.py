import alsaaudio

channel_names = ['front-left','front-right']

def get_all():
    controls = {}
    for name in alsaaudio.mixers():
        m = alsaaudio.Mixer(name)
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
    if control:
        mixer = alsaaudio.Mixer(control)
    else:
        mixer = alsaaudio.Mixer()

    if channel:
        mixer.setvolume(volume, channel_names.index(channel))
    else:
        mixer.setvolume(volume)
