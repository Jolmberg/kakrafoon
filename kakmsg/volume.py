from marshmallow import Schema, fields
import marshmallow

class Channel(object):
    def __init__(self, name, volume):
        self.name = name
        self.volume = volume

class Control(object):
    def __init__(self, name, channels):
        self.name = name
        self.channels = channels

class Volume(object):
    def __init__(self, controls):
        self.controls = controls

class SetRequest(object):
    def __init__(self, volume, channel=None, control=None):
        self.control = control
        self.channel = channel
        self.volume = volume


class ChannelSchema(Schema):
    name = fields.Str(required=True)
    volume = fields.Int(required=True)

    @marshmallow.post_load
    def make_channel(self, data):
        return Channel(**data)

class ControlSchema(Schema):
    name = fields.Str(required=True)
    channels = fields.Nested(ChannelSchema, many=True)

    @marshmallow.post_load
    def make_control(self, data):
        return Control(**data)

class VolumeSchema(Schema):
    controls = fields.Nested(ControlSchema, many=True)

    @marshmallow.post_load
    def make_volume(self, data):
        return Volume(**data)

class SetRequestSchema(Schema):
    control = fields.Str(missing=None)
    channel = fields.Str(missing=None)
    volume = fields.Int(required=True)

    @marshmallow.post_load
    def make_setrequest(self, data):
        return SetRequest(**data)
