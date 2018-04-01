from marshmallow import Schema, fields
import marshmallow

class Channel(object):
    def __init__(self, name, volume):
        self.name = name
        self.volume = volume

class Mixer(object):
    def __init__(self, name, channels):
        self.name = name
        self.channels = channels

class Volume(object):
    def __init__(self, mixers):
        self.mixers = mixers

class SetRequest(object):
    def __init__(self, volume, channel=None, mixer=None):
        self.mixer = mixer
        self.channel = channel
        self.volume = volume


class ChannelSchema(Schema):
    name = fields.Str(required=True)
    volume = fields.Int(required=True)

    @marshmallow.post_load
    def make_channel(self, data):
        return Channel(**data)

class MixerSchema(Schema):
    name = fields.Str(required=True)
    channels = fields.Nested(ChannelSchema, many=True)

    @marshmallow.post_load
    def make_mixer(self, data):
        return Mixer(**data)

class VolumeSchema(Schema):
    mixers = fields.Nested(MixerSchema, many=True)

    @marshmallow.post_load
    def make_volume(self, data):
        return Volume(**data)

class SetRequestSchema(Schema):
    mixer = fields.Str(missing=None)
    channel = fields.Str(missing=None)
    volume = fields.Int(required=True)

    @marshmallow.post_load
    def make_setrequest(self, data):
        return SetRequest(**data)
